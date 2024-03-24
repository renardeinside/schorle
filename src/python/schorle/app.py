import asyncio
import mimetypes
from functools import partial
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI
from loguru import logger
from starlette.responses import FileResponse
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocketDisconnect

from schorle.document import Document
from schorle.theme import Theme
from schorle.utils import RunningMode, get_running_mode

ASSETS_PATH = Path(str(files("schorle"))) / Path("assets")


def favicon() -> FileResponse:
    favicon_path = ASSETS_PATH / "base" / "favicon.svg"
    return FileResponse(favicon_path, media_type="image/svg+xml")


def get_file(file_name: str, *, ext: str = "base") -> FileResponse:
    file_path = ASSETS_PATH / ext / file_name
    mime_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(file_path, media_type=mime_type)


async def _dev_ws_handler(websocket):
    logger.info("Dev websocket connected")
    await websocket.accept()
    while True:
        await asyncio.sleep(0.1)
        try:
            await websocket.receive_text()
        except WebSocketDisconnect:
            break


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK, lang: str = "en", extra_assets: list | None = None) -> None:
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name:path}", response_class=FileResponse)(get_file)
        self.backend.get("/favicon.svg", response_class=FileResponse)(favicon)
        self.theme: Theme = theme
        self.extra_assets = extra_assets
        self.lang = lang

        if get_running_mode() == RunningMode.DEV:
            self._with_dev_tools = True
            self.backend.get("/_schorle/dev/assets/{file_name:path}", response_class=FileResponse)(
                partial(get_file, ext="dev")
            )
            self.backend.add_websocket_route("/_schorle/dev/_events", _dev_ws_handler, name="dev_ws")

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        This method is called by uvicorn when the server is started.
        """
        await self.backend(scope=scope, receive=receive, send=send)

    @property
    def doc(self) -> Document:
        return Document(
            theme=self.theme, lang=self.lang, extra_assets=self.extra_assets, with_dev_tools=self._with_dev_tools
        )
