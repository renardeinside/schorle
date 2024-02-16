import asyncio
import pkgutil
from asyncio import iscoroutinefunction
from collections.abc import Callable
from functools import partial
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI
from loguru import logger
from lxml import etree
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import FileResponse, HTMLResponse, PlainTextResponse
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from schorle.document import Document
from schorle.emitter import PageEmitter
from schorle.models import HtmxMessage
from schorle.page import Page
from schorle.theme import Theme
from schorle.utils import RunningMode, get_running_mode, render_in_context


def favicon() -> FileResponse:
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
    def __init__(self, theme: Theme = Theme.DARK, lang: str = "en", extra_assets: list | None = None) -> None:
        self._pages: dict[str, Page] = {}
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name:path}")(assets)
        self.backend.add_websocket_route("/_schorle/events", partial(EventsEndpoint, pages=self._pages))
        self.backend.get("/favicon.svg", response_model=None)(favicon)
        self.theme: Theme = theme
        self.extra_assets = extra_assets
        self.lang = lang

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

        if get_running_mode() == RunningMode.DEV:
            logger.info("Adding dev meta tags...")

        doc = Document(
            title="Schorle",
            page=page,
            theme=self.theme,
            with_dev_meta=get_running_mode() == RunningMode.DEV,
            extra_assets=self.extra_assets,
            lang=self.lang,
        )
        logger.debug(f"Rendering page: {page} with theme: {self.theme}...")

        lxml_element = render_in_context(doc)
        rendered = etree.tostring(lxml_element, pretty_print=True, doctype="<!DOCTYPE html>").decode("utf-8")
        response = HTMLResponse(rendered, status_code=200)

        logger.info(f"Adding page to cache with token: {doc.csrf_token}")

        self._pages[str(doc.csrf_token)] = page

        logger.debug("Page rendered.")

        return response


class EventsEndpoint(WebSocketEndpoint):
    encoding = "text"

    def __init__(self, scope, receive, send, pages: dict[str, Page]) -> None:
        super().__init__(scope, receive, send)
        self._page: Page | None = None
        self._pages: dict[str, Page] = pages
        self.page_emitter_task = None

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
            self.page_emitter_task = asyncio.create_task(PageEmitter(page).emit(websocket))
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
            reactive = self._page.reactives.get(message.headers.trigger_element_id)
            if reactive:
                logger.debug(f"Events found reactive: {reactive}")
                _callback = reactive.get(message.headers.trigger_type)
                if _callback:
                    logger.debug(f"Events found callback: {_callback}")
                    if message.headers.trigger_name is not None:
                        _value = getattr(message, message.headers.trigger_name)
                        _callback(_value)
                    else:
                        _callback()
                    logger.debug("Events callback executed.")
                else:
                    logger.error(f"Events no callback found for type: {message.headers.trigger_type}")
            else:
                logger.error(f"Events no reactive found for id: {message.headers.trigger_element_id}")

        else:
            logger.error("No page found, closing websocket...")
            await ws.close()

    async def on_disconnect(self, _: WebSocket, close_code: int) -> None:
        logger.info(f"Events disconnected with code: {close_code}")
        if self.page_emitter_task:
            self.page_emitter_task.cancel()
            logger.info("Events emitter task cancelled.")


def wrap_in_coroutine(func: Callable) -> Callable:
    if iscoroutinefunction(func):
        return func
    else:

        async def _wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return _wrapper
