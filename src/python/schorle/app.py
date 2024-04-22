import mimetypes
from importlib.resources import files
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from starlette.responses import FileResponse, HTMLResponse
from starlette.types import Receive, Scope, Send

from schorle.component import Component
from schorle.document import Document
from schorle.theme import Theme

ASSETS_PATH = Path(str(files("schorle"))) / Path("assets")


def favicon() -> FileResponse:
    favicon_path = ASSETS_PATH / "static" / "favicon.svg"
    return FileResponse(favicon_path, media_type="image/svg+xml")


def get_file(file_name: str) -> FileResponse:
    file_path = ASSETS_PATH / file_name
    mime_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(file_path, media_type=mime_type)


SESSION_ID_HEADER = "X-Schorle-Session-Id"


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK, lang: str = "en", extra_assets: Callable[..., None] | None = None):
        self.backend = FastAPI()
        self.backend.get("/_schorle/{file_name:path}", response_class=FileResponse)(get_file)
        self.backend.get("/favicon.svg", response_class=FileResponse)(favicon)
        self.theme = theme
        self.lang = lang
        self.extra_assets = extra_assets

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        This method is called by uvicorn when the server is started.
        """
        await self.backend(scope=scope, receive=receive, send=send)

    def get(self, path: str):
        def decorator(func: Callable[..., Component]):
            @self.backend.get(path, response_class=HTMLResponse)
            async def wrapper():
                doc = Document(page=func(), theme=self.theme, lang=self.lang, extra_assets=self.extra_assets)
                return doc.to_response()

        return decorator
