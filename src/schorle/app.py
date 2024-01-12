import pkgutil
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

from schorle.elements.html import BodyWithPage, EventHandler, Html, Meta, MorphWrapper
from schorle.elements.page import Page
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

        handler = EventHandler(content=page)
        body = BodyWithPage(wrapper=MorphWrapper(handler=handler))
        logger.debug(f"Rendering page: {page} with theme: {self.theme}...")
        html = Html(body=body, theme=self.theme)

        if get_running_mode() == RunningMode.DEV:
            logger.info("Adding dev meta tags...")
            html.head.dev_meta = Meta(name="schorle-dev", content="true")

        response = HTMLResponse(html.render(), status_code=200)
        logger.info(f"Adding page to cache with token: {html.head.csrf_meta.content}")
        self._pages[html.head.csrf_meta.content] = page

        logger.debug("Page rendered.")

        return response


class EventsEndpoint(WebSocketEndpoint):
    encoding = "text"

    def __init__(self, scope, receive, send, pages: dict[str, Page]) -> None:
        super().__init__(scope, receive, send)
        self._page_binding_task = None
        self._page_updates_task = None
        self._page: Page | None = None
        self._pages: dict[str, Page] = pages

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

    async def on_receive(self, _: WebSocket, data: str) -> None:
        logger.warning(f"Events received message: {data}")

    async def on_disconnect(self, _: WebSocket, close_code: int) -> None:
        logger.info(f"Events disconnected with code: {close_code}")
