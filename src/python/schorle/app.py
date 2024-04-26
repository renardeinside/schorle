import mimetypes
from functools import partial
from pathlib import Path
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI
from loguru import logger
from starlette.responses import FileResponse, HTMLResponse
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from schorle.component import Component
from schorle.document import Document
from schorle.events import EventsEndpoint
from schorle.headers import SESSION_ID_HEADER
from schorle.session import Session
from schorle.theme import Theme
from schorle.utils import ASSETS_PATH, RunningMode, get_running_mode


def favicon() -> FileResponse:
    favicon_path = ASSETS_PATH / "static" / "favicon.svg"
    return FileResponse(favicon_path, media_type="image/svg+xml")


def get_file(file_name: str, sub_path: Path | None = None) -> FileResponse | HTMLResponse:
    file_path = ASSETS_PATH / file_name if not sub_path else ASSETS_PATH / sub_path / file_name

    if file_path.exists() and file_path.is_file():
        mime_type, _ = mimetypes.guess_type(file_path)

        response = FileResponse(file_path, media_type=mime_type)
        logger.info(f"Sending file: {file_path} with suffixes: {file_path.suffixes}")
        if ".br" in file_path.suffixes:
            response.headers["Content-Encoding"] = "br"
            logger.info(f"Using brotli compression for file {file_path}")
        return response
    else:
        return HTMLResponse(status_code=404)


class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self):
        session_id = f"sle-{uuid4()}"
        new_session = Session(session_id)
        self.sessions[session_id] = new_session
        return new_session

    def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]


class Schorle:
    def __init__(
        self,
        theme: Theme = Theme.DARK,
        lang: str = "en",
        extra_assets: Callable[..., None] | None = None,
        title: str = "Schorle",
    ):
        self.backend = FastAPI()
        self.backend.get("/_schorle/{file_name:path}", response_model=None)(get_file)
        self.backend.get("/_schorle/dist/{file_name:path}", response_model=None)(partial(get_file, sub_path="dist"))
        self.backend.get("/favicon.svg", response_class=FileResponse)(favicon)
        self.theme = theme
        self.lang = lang
        self.extra_assets = extra_assets
        self.title = title
        self.session_manager = SessionManager()
        self.backend.state.session_manager = self.session_manager
        self.backend.add_websocket_route("/_schorle/events", EventsEndpoint)

        if get_running_mode() == RunningMode.DEV:
            self.backend.add_websocket_route("/_schorle/dev/events", self.dev_handler)

    @staticmethod
    async def dev_handler(websocket: WebSocket):
        await websocket.accept()
        while True:
            try:
                _ = await websocket.receive_json()
            except Exception:
                break

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        This method is called by uvicorn when the server is started.
        """
        await self.backend(scope=scope, receive=receive, send=send)

    def get(self, path: str):
        def decorator(func: Callable[..., Component]):
            @self.backend.get(path, response_class=HTMLResponse)
            async def wrapper():
                doc = Document(
                    page=func(),
                    theme=self.theme,
                    lang=self.lang,
                    extra_assets=self.extra_assets,
                    title=self.title,
                    with_dev_tools=get_running_mode() == RunningMode.DEV,
                )
                new_session = self.session_manager.create_session()
                response = doc.to_response(new_session)
                response.set_cookie(SESSION_ID_HEADER, new_session.uuid)
                return response

        return decorator
