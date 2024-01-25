import asyncio
import pkgutil
from asyncio import Task, iscoroutinefunction
from functools import partial
from importlib.resources import files
from pathlib import Path
from typing import Callable, Union

from fastapi import FastAPI
from loguru import logger
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import FileResponse, HTMLResponse, PlainTextResponse
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from schorle.dynamics.base import Reactive
from schorle.elements.base.element import Element
from schorle.elements.html import BodyWithPage, EventHandler, Html, Meta, MorphWrapper
from schorle.elements.page import Page
from schorle.models import HtmxMessage
from schorle.theme import Theme
from schorle.utils import RunningMode, get_running_mode


def favicon() -> Union[FileResponse, HTMLResponse]:
    package_path = files("schorle")
    favicon_path = Path(str(package_path)) / "assets" / "favicon.svg"
    return FileResponse(favicon_path, media_type="image/svg+xml")


def assets(file_name: str) -> PlainTextResponse:
    _bundle = pkgutil.get_data("schorle", f"assets/{file_name}")
    if _bundle:
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)
    else:
        return PlainTextResponse(f"File not found: {file_name}", status_code=404)


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK) -> None:
        self._pages: dict[str, Page] = {}
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name:path}")(assets)
        self.backend.add_websocket_route("/_schorle/events", partial(EventsEndpoint, pages=self._pages))
        self.backend.get("/favicon.svg", response_model=None)(favicon)
        self.theme: Theme = theme

    def get(self, path: str):
        def decorator(func: Callable[..., Page]):
            self.backend.get(path, response_class=HTMLResponse)(partial(self.render_to_response, func))
            return func

        return decorator

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        This method is called by uvicorn when the server is started.
        """
        await self.backend(scope=scope, receive=receive, send=send)

    async def render_to_response(self, page_provider: Callable[..., Page]) -> HTMLResponse:
        page = page_provider()

        logger.info(f"Rendering page: {page}...")

        page.inject_page_reference()
        handler = EventHandler(content=page)
        body = BodyWithPage(wrapper=MorphWrapper(handler=handler))
        logger.debug(f"Rendering page: {page} with theme: {self.theme}...")
        html = Html(body=body, theme=self.theme)

        if get_running_mode() == RunningMode.DEV:
            logger.info("Adding dev meta tags...")
            html.head.dev_meta = Meta(name="schorle-dev", content="true")

        before_render_tasks = []
        for element in page.traverse():
            if isinstance(element, Element):
                for _method in element.get_methods_with_attribute("before_render"):
                    method_task = asyncio.create_task(_method())
                    before_render_tasks.append(method_task)

        await asyncio.gather(*before_render_tasks)

        response = HTMLResponse(html.render(), status_code=200)
        logger.info(f"Adding page to cache with token: {html.head.csrf_meta.content}")

        self._pages[html.head.csrf_meta.content] = page

        logger.debug("Page rendered.")

        return response


class EventsEndpoint(WebSocketEndpoint):
    encoding = "text"

    def __init__(self, scope, receive, send, pages: dict[str, Page]) -> None:
        super().__init__(scope, receive, send)
        self._page: Page | None = None
        self._pages: dict[str, Page] = pages
        self._updates_emitter_task: Task | None = None

    async def _updates_emitter(self, page: Page, ws: WebSocket):
        emitters = []

        async def _emit(_element: Element, field: Reactive):
            async for _ in field:
                logger.debug(f"Events emitting element: {_element}")
                page.inject_page_reference()
                await ws.send_text(_element.render())
                logger.debug(f"Events emitted element: {_element}")

        try:
            for element in page.traverse():
                if isinstance(element, Element):
                    observable_fields = element.get_observable_fields()
                    for field in observable_fields:
                        emitters.append(_emit(element, field))
        except Exception as e:
            logger.error(f"Events emitter failed with exception: {e}")

        await asyncio.gather(*emitters)

    async def on_connect(self, websocket: WebSocket) -> None:
        token = websocket.query_params.get("token")
        if not token:
            logger.error("No token provided.")
            await websocket.close()
            return
        page: Page | None = self._pages.get(token)
        if page:
            await websocket.accept()
            self._page = page
            self._updates_emitter_task = asyncio.create_task(self._updates_emitter(page, websocket))
            logger.info("Events connected.")

        elif not page and get_running_mode() == RunningMode.DEV:
            logger.info("Sending reload message to client...")
            await websocket.accept()
            await websocket.send_text("reload")  # standard schorle reload message
            await websocket.close()
            return
        else:
            logger.error(f"No page found for token: {token}")
            await websocket.close()
            return

    async def on_receive(self, ws: WebSocket, data: str) -> None:
        logger.warning(f"Events received message: {data}")
        message = HtmxMessage.model_validate_json(data)
        logger.debug(f"Events received message: {message}")
        if self._page:
            _element = self._page.find_by_id(message.headers.trigger_element_id)
            if _element and isinstance(_element, Element):
                logger.debug(f"Events found element: {_element}")
                method = _element.reactive_methods.get(message.headers.trigger_type)
                if not method:
                    msg = (
                        f"No method found for trigger: {message.headers.trigger_element_id} "
                        f"{message.headers.trigger_type}"
                    )
                    logger.warning(msg)
                else:
                    logger.debug(f"Events found method: {method}")
                    wrapped_method = wrap_in_coroutine(method)
                    if message.headers.trigger_type == "change" and _element.name:
                        new_value = getattr(message, _element.name)
                        await wrapped_method(new_value)
                    else:
                        await wrapped_method()
                    logger.debug(f"Events executed method: {method}")
            else:
                logger.error(f"No reactive element found for id: {message.headers.trigger_element_id}")
        else:
            logger.error("No page found, closing websocket...")
            await ws.close()

    async def on_disconnect(self, _: WebSocket, close_code: int) -> None:
        logger.info(f"Events disconnected with code: {close_code}")
        if self._updates_emitter_task:
            self._updates_emitter_task.cancel()
            logger.info("Events emitter task cancelled.")


def wrap_in_coroutine(func: Callable) -> Callable:
    if iscoroutinefunction(func):
        return func
    else:

        async def _wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return _wrapper
