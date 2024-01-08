import asyncio
import json
import pkgutil
from functools import partial
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from loguru import logger
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse
from starlette.websockets import WebSocket

from schorle.elements.html import BodyWithPage, EventHandler, Html, Meta, MorphWrapper
from schorle.elements.page import Page
from schorle.models import HtmxMessage
from schorle.observable import Subscriber
from schorle.theme import Theme
from schorle.utils import RunningMode, get_running_mode


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK) -> None:
        self._pages: dict[str, Page] = {}
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name:path}")(self._assets)
        self.backend.add_websocket_route("/_schorle/events", partial(EventsEndpoint, pages=self._pages))
        self.backend.get("/favicon.svg")(self._favicon)
        self.theme: Theme = theme

    def _favicon(self):
        loader: SourceFileLoader | None = pkgutil.get_loader("schorle")
        if loader is None:
            raise RuntimeError("Could not find loader for schorle package.")
        else:
            loader_path = Path(loader.path).parent / "assets" / "logo.svg"
            return FileResponse(loader_path, media_type="image/svg+xml")

    def get(self, path: str):
        def decorator(func: Callable[..., Page]):
            self.backend.get(path, response_class=HTMLResponse)(partial(self.render_to_response, func))
            return func

        return decorator

    async def render_to_response(self, page_provider: Callable[..., Page]) -> HTMLResponse:
        page = page_provider()
        logger.info(f"Rendering page: {page}...")
        before_render_tasks = page.get_all_pre_render_tasks()

        if before_render_tasks:
            logger.info(f"Running pre-renders: {before_render_tasks}")
            try:
                await asyncio.gather(*before_render_tasks)
            except asyncio.CancelledError:
                logger.info("Pre-rendering tasks cancelled.")
                for task in before_render_tasks:
                    task.cancel()

        handler = EventHandler(content=page)
        body = BodyWithPage(wrapper=MorphWrapper(handler=handler))
        logger.debug(f"Rendering page: {page} with theme: {self.theme}...")
        html = Html(body=body, **{"data-theme": self.theme})

        if get_running_mode() == RunningMode.UVICORN_DEV:
            logger.info("Adding dev meta tags...")
            html.head.dev_meta = Meta(name="schorle-dev", content="true")

        response = HTMLResponse(html.render(), status_code=200)
        logger.info(f"Adding page to cache with token: {html.head.csrf_meta.content}")
        self._pages[html.head.csrf_meta.content] = page

        logger.debug("Page rendered.")

        return response

    @staticmethod
    async def _assets(file_name: str) -> PlainTextResponse:
        _bundle = pkgutil.get_data("schorle", f"assets/{file_name}")
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)


class EventsEndpoint(WebSocketEndpoint):
    encoding = "text"

    def __init__(self, scope, receive, send, pages: dict[str, Page]) -> None:
        super().__init__(scope, receive, send)
        self._page_binding_task = None
        self._page_updates_task = None
        self._page = None
        self._pages = pages

    async def _page_updates_emitter(self, ws: WebSocket) -> None:
        subscriber = Subscriber()
        self._page.subscribe_all_elements(subscriber)

        logger.info("Starting the page updates emitter...")
        async for element in subscriber:
            rendered = element.render()
            logger.info(f"Sending page updates to client: {rendered}")
            await ws.send_text(rendered)

    async def _binding_updates_emitter(self) -> None:
        binding_tasks = self._page.get_all_binding_tasks()
        await asyncio.gather(*binding_tasks)

    async def on_connect(self, websocket: WebSocket) -> None:
        token = websocket.query_params.get("token")
        page = self._pages.get(token)
        if not page:
            if get_running_mode() == RunningMode.UVICORN_DEV:
                logger.info("Sending reload message to client...")
                await websocket.accept()
                await websocket.send_text("reload")  # standard schorle reload message
                await websocket.close()
                return
            else:
                logger.error(f"No page found for token: {token}")
                await websocket.close()
                return

        await websocket.accept()
        self._page = page
        self._page_updates_task = asyncio.create_task(self._page_updates_emitter(websocket))
        self._page_binding_task = asyncio.create_task(self._binding_updates_emitter())

        on_load_tasks = self._page.get_all_on_loads()
        logger.info(f"Provided on_loads: {on_load_tasks}")
        if on_load_tasks:
            logger.info(f"Adding on_loads: {on_load_tasks}")
            tasks = [asyncio.create_task(t()) for t in on_load_tasks]
            await asyncio.gather(*tasks)

        logger.info("Events connected.")

    async def on_receive(self, _: WebSocket, data: str) -> None:
        logger.warning(f"Events received message: {data}")
        message = HtmxMessage(**json.loads(data))

        _element = self._page.find_by_id(message.headers.trigger)

        if _element is None:
            logger.error(f"No element found for trigger: {message.headers.trigger}")
            return

        if _element.on_click is not None:
            logger.info(f"Calling on_click handlers for element {_element.element_id}")
            await _element.on_click()

    async def on_disconnect(self, _: WebSocket, close_code: int) -> None:
        logger.info(f"Events disconnected with code: {close_code}")
        for task in (self._page_updates_task, self._page_binding_task):
            if task is not None:
                task.cancel()
