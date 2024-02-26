import asyncio
import mimetypes
from asyncio import Task, iscoroutinefunction
from collections.abc import Callable
from functools import partial
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request, UploadFile
from loguru import logger
from lxml import etree
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import FileResponse, HTMLResponse
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from schorle.controller import RenderController
from schorle.document import Document
from schorle.emitter import PageEmitter
from schorle.models import ClientMessage
from schorle.page import Page
from schorle.theme import Theme
from schorle.utils import RunningMode, get_running_mode

ASSETS_PATH = Path(str(files("schorle"))) / Path("assets")


def favicon() -> FileResponse:
    favicon_path = ASSETS_PATH / "favicon.svg"
    return FileResponse(favicon_path, media_type="image/svg+xml")


def assets(file_name: str) -> FileResponse:
    file_path = ASSETS_PATH / file_name
    mime_type, _ = mimetypes.guess_type(file_path)
    headers = {"Cache-Control": "no-cache, no-store"} if get_running_mode() == RunningMode.DEV else {}
    return FileResponse(file_path, media_type=mime_type, headers=headers)


PATH_HEADER = "X-Schorle-Session-Path"
SESSION_ID_HEADER = "X-Schorle-Session-Id"
TRIGGER_ID_HEADER = "X-Schorle-Trigger-Id"


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK, lang: str = "en", extra_assets: list | None = None) -> None:
        self._pages: dict[str, Page] = {}
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name:path}", response_class=FileResponse)(assets)
        self.backend.post("/_schorle/upload")(self._file_upload)
        self.backend.add_websocket_route("/_schorle/events", partial(EventsEndpoint, pages=self._pages))
        self.backend.get("/favicon.svg", response_class=FileResponse)(favicon)
        self.theme: Theme = theme
        self.extra_assets = extra_assets
        self.lang = lang

    def get(self, path: str):
        def decorator(func: Callable[..., Page]):
            self.backend.get(path, response_class=HTMLResponse)(partial(self.render_to_response, func, path))
            return func

        return decorator

    async def _file_upload(self, uploaded_files: list[UploadFile], request: Request):
        trigger_id = request.headers.get(TRIGGER_ID_HEADER)
        session_id = request.cookies.get(SESSION_ID_HEADER)

        if (
            not trigger_id
            or not session_id
            or session_id not in self._pages
            or trigger_id not in self._pages[session_id].reactives
        ):
            logger.warning(f"Invalid file upload request: {request}")
            return HTMLResponse("Invalid request.", status_code=400)
        else:
            reactive = self._pages[session_id].reactives[trigger_id]
            callback = reactive.get("change")
            if callback:
                _arg = uploaded_files[0] if len(uploaded_files) == 1 else uploaded_files
                await callback(_arg)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        This method is called by uvicorn when the server is started.
        """
        await self.backend(scope=scope, receive=receive, send=send)

    async def render_to_response(self, page_provider: Callable[..., Page], path: str) -> HTMLResponse:
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

        with RenderController() as rc:
            lxml_element = rc.render(doc)

        rendered = etree.tostring(lxml_element, pretty_print=True, doctype="<!DOCTYPE html>").decode("utf-8")
        logger.debug(rendered)
        response = HTMLResponse(rendered, status_code=200)
        _session_id = str(uuid4())
        response.set_cookie(SESSION_ID_HEADER, _session_id)
        response.set_cookie(PATH_HEADER, path)
        self._pages[_session_id] = page

        logger.debug("Page rendered.")

        return response


class EventsEndpoint(WebSocketEndpoint):
    encoding = "bytes"

    def __init__(self, scope, receive, send, pages: dict[str, Page]) -> None:
        super().__init__(scope, receive, send)
        self._page: Page | None = None
        self._pages: dict[str, Page] = pages
        self.page_emitter_task: Task | None = None

    async def on_connect(self, websocket: WebSocket) -> None:
        for expected_header in [PATH_HEADER, SESSION_ID_HEADER]:
            if expected_header not in websocket.cookies:
                logger.error(f"Missing header: {expected_header}")
                await websocket.close(1011, f"Missing header: {expected_header}")
                return

        session_id = websocket.cookies[SESSION_ID_HEADER]
        page: Page | None = self._pages.get(session_id)

        if page:
            await websocket.accept()
            self._page = page
            self.page_emitter_task = asyncio.create_task(PageEmitter(page).emit(websocket))
            page.io = websocket
            logger.info("Events connected.")
        else:
            await websocket.close(1001, "Page not found.")
            return

    async def on_receive(self, ws: WebSocket, data: bytes) -> None:
        logger.warning("Events received message, decoding it")
        try:
            message = ClientMessage.decode(data)
            logger.debug(f"Events parsed message: {message}")

        except ValueError as e:
            msg = f"Cannot parse message: {e}, format is invalid."
            logger.error(msg)
            await ws.close(code=1011, reason=msg)
            return

        if self._page:
            reactive = self._page.reactives.get(message.target)
            if reactive:
                _callback = reactive.get(message.trigger)
                if _callback:
                    logger.debug("Events found callback, processing it")
                    _cb = partial(_callback, message.value)
                    # TODO: catch exceptions in _cb
                    asyncio.ensure_future(_cb())  # noqa: RUF006

                else:
                    logger.error(f"Events no callback found for type: {message.trigger}")
            else:
                logger.error(f"Events no reactive found for id: {message.target}")

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
