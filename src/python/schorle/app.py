import mimetypes
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI
from starlette.responses import FileResponse
from starlette.types import Receive, Scope, Send

from schorle.document import Document
from schorle.theme import Theme

ASSETS_PATH = Path(str(files("schorle"))) / Path("assets")


def favicon() -> FileResponse:
    favicon_path = ASSETS_PATH / "favicon.svg"
    return FileResponse(favicon_path, media_type="image/svg+xml")


def assets(file_name: str) -> FileResponse:
    file_path = ASSETS_PATH / file_name
    mime_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(file_path, media_type=mime_type)


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK, lang: str = "en", extra_assets: list | None = None) -> None:
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name:path}", response_class=FileResponse)(assets)
        self.backend.get("/favicon.svg", response_class=FileResponse)(favicon)
        self.theme: Theme = theme
        self.extra_assets = extra_assets
        self.lang = lang

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        This method is called by uvicorn when the server is started.
        """
        await self.backend(scope=scope, receive=receive, send=send)

    @property
    def doc(self) -> Document:
        return Document(theme=self.theme, lang=self.lang, extra_assets=self.extra_assets)
