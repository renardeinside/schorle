import mimetypes
from collections.abc import Callable
from functools import partial
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from loguru import logger
from lxml import etree
from starlette.responses import FileResponse, HTMLResponse
from starlette.types import Receive, Scope, Send

from schorle.controller import RenderController
from schorle.document import Document
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
    return FileResponse(file_path, media_type=mime_type)


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK, lang: str = "en", extra_assets: list | None = None) -> None:
        self._pages: dict[str, Page] = {}
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name:path}", response_class=FileResponse)(assets)
        self.backend.get("/favicon.svg", response_class=FileResponse)(favicon)
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

        with RenderController() as rc:
            lxml_element = rc.render(doc)

        rendered = etree.tostring(lxml_element, pretty_print=True, doctype="<!DOCTYPE html>").decode("utf-8")
        response = HTMLResponse(rendered, status_code=200)
        _session_id = str(uuid4())
        self._pages[_session_id] = page

        logger.debug("Page rendered.")

        return response
