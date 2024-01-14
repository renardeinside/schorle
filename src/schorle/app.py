import asyncio
import pkgutil
from asyncio import Task
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

from schorle.elements.base.element import Element
from schorle.elements.button import Button
from schorle.elements.html import BodyWithPage, EventHandler, Html, Meta, MorphWrapper
from schorle.elements.page import Page
from schorle.models import HtmxMessage
from schorle.state import State, inject_state
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
        self._state_class: type[State] | None = None
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

    def state(self, state_class: type[State]):
        logger.info(f"Registering state class: {state_class}...")
        self._state_class = state_class
        logger.info(f"Registered state class: {state_class}.")
        return state_class

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        This method is called by uvicorn when the server is started.
        """
        await self.backend(scope=scope, receive=receive, send=send)

    async def render_to_response(self, page_provider: Callable[..., Page]) -> HTMLResponse:
        page = page_provider()
        logger.info(f"Rendering page: {page}...")

        handler = EventHandler(content=page)
        body = BodyWithPage(wrapper=MorphWrapper(handler=handler))
        logger.debug(f"Rendering page: {page} with theme: {self.theme}...")
        html = Html(body=body, theme=self.theme)

        if get_running_mode() == RunningMode.DEV:
            logger.info("Adding dev meta tags...")
            html.head.dev_meta = Meta(name="schorle-dev", content="true")

        response = HTMLResponse(html.render(), status_code=200)
        logger.info(f"Adding page to cache with token: {html.head.csrf_meta.content}")
        state_instance = self._state_class() if self._state_class else None
        page.state = state_instance

        for element in page.traverse():
            injectables = element.get_injectables()
            if injectables:
                logger.debug(f"Injecting into element: {element}...")
                for injectable in injectables:
                    logger.debug(f"Injecting into {injectable} on element: {element}...")
                    injected = inject_state(state_instance, injectable)
                    setattr(element, injectable.__name__, injected)
                    logger.debug(f"Injected into {injectable} on element: {element}.")

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
        for element in page.traverse():
            if isinstance(element, Element):
                emitters.append(element.updates_emitter)

        async def _emit(emitter):
            async for _element in emitter():
                await ws.send_text(_element.render())

        tasks = [asyncio.create_task(_emit(emitter)) for emitter in emitters]
        await asyncio.gather(*tasks)

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
            _element = self._page.find_by_id(message.headers.trigger)
            if _element:
                logger.debug(f"Events found element: {_element}")
                if isinstance(_element, Button):
                    logger.debug(f"Events found button: {_element}, executing on_click...")
                    await _element.on_click()
                    logger.debug(f"Events executed on_click for button: {_element}")
            else:
                logger.error(f"No element found for id: {message.headers.trigger}")
        else:
            logger.error("No page found, closing websocket...")
            await ws.close()

    async def on_disconnect(self, _: WebSocket, close_code: int) -> None:
        logger.info(f"Events disconnected with code: {close_code}")
        if self._updates_emitter_task:
            self._updates_emitter_task.cancel()
            logger.info("Events emitter task cancelled.")
