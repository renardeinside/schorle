import pkgutil
from typing import Callable

from fastapi import FastAPI
from loguru import logger
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.websockets import WebSocket

from schorle.elements.html import BodyClasses, BodyWithPageAndDeveloperTools, EventHandler, Html, MorphWrapper
from schorle.elements.page import Page
from schorle.models import HtmxMessage
from schorle.theme import Theme


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK) -> None:
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name}")(self._assets)
        self.backend.websocket("/_schorle/devtools")(self._devtools_handler)
        self.backend.websocket("/_schorle/events")(self._events_handler)
        self._pages: dict[str, Page] = {}
        self.theme: Theme = theme

    def get(self, path: str):
        def decorator(func: Callable[..., Page]):
            self.backend.get(path)(lambda: self.render_to_response(page=func(), path=path))
            return func

        return decorator

    def render_to_response(
        self, page: Page, path: str, body_class: BodyClasses = BodyWithPageAndDeveloperTools
    ) -> HTMLResponse:
        handler = EventHandler(content=page)
        body = body_class(wrapper=MorphWrapper(handler=handler))
        logger.debug(f"Rendering page: {page} with theme: {self.theme}...")
        html = Html(body=body, **{"data-theme": self.theme})
        response = HTMLResponse(html.render(), status_code=200)
        logger.debug(f"Response: {response.body.decode('utf-8')}")
        self._pages[path] = page
        return response

    @staticmethod
    async def _assets(file_name: str) -> PlainTextResponse:
        _bundle = pkgutil.get_data("schorle", f"assets/{file_name}")
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)

    async def _devtools_handler(self, ws: WebSocket) -> None:
        await ws.accept()
        logger.info("Devtools connected.")
        async for message in ws.iter_text():
            logger.info(f"Devtools received message: {message}")

        logger.info("Devtools disconnected.")

    async def _events_handler(self, ws: WebSocket) -> None:
        await ws.accept()
        _path = ws.query_params.get("path")
        logger.info(f"Events connected to path: {_path}")
        async for raw_message in ws.iter_json():
            message = HtmxMessage(**raw_message)
            logger.info(f"Events received message: {message}")
            _page = self._pages.get(_path)
            if _page is None:
                logger.error(f"No page found for path: {_path}")
                continue

            _element = _page.find_by_id(message.headers.trigger)
            if _element is None:
                logger.error(f"No element found for trigger: {message.headers.trigger}")
                continue

            if _element.on_click is not None:
                logger.info(f"Calling on_click handlers for element {_element.element_id}")
                await _element.on_click()

        logger.info("Events disconnected.")
