import mimetypes
from importlib.resources import files
from pathlib import Path
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI
from starlette.responses import FileResponse, HTMLResponse
from starlette.types import Receive, Scope, Send

from schorle.component import Component
from schorle.document import Document
from schorle.events import EventsEndpoint
from schorle.headers import SESSION_ID_HEADER
from schorle.session import Session
from schorle.theme import Theme

ASSETS_PATH = Path(str(files("schorle"))) / Path("assets")


def favicon() -> FileResponse:
    favicon_path = ASSETS_PATH / "static" / "favicon.svg"
    return FileResponse(favicon_path, media_type="image/svg+xml")


def get_file(file_name: str) -> FileResponse:
    file_path = ASSETS_PATH / file_name
    mime_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(file_path, media_type=mime_type)


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
        self.backend.get("/_schorle/{file_name:path}", response_class=FileResponse)(get_file)
        self.backend.get("/favicon.svg", response_class=FileResponse)(favicon)
        self.theme = theme
        self.lang = lang
        self.extra_assets = extra_assets
        self.title = title
        self.session_manager = SessionManager()
        self.backend.state.session_manager = self.session_manager
        self.backend.add_websocket_route("/_schorle/events", EventsEndpoint)

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
                    page=func(), theme=self.theme, lang=self.lang, extra_assets=self.extra_assets, title=self.title
                )
                new_session = self.session_manager.create_session()
                response = doc.to_response(new_session)
                response.set_cookie(SESSION_ID_HEADER, new_session.uuid)
                return response

        return decorator
