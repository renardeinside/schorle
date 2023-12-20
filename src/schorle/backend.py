import pkgutil

from fastapi import FastAPI
from loguru import logger
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.websockets import WebSocket

from schorle.app import Schorle
from schorle.elements.html import BodyWithPageAndDeveloperTools


class BackendApp:
    def __init__(self, app: FastAPI | None = None) -> None:
        self.app = FastAPI() if app is None else app
        self.app.get("/_schorle/assets/bundle.js")(self._assets)
        self.app.get("/{path:path}")(self._dynamic_handler)
        self.app.websocket("/_schorle/devtools")(self._devtools_handler)
        self._instance: Schorle | None = None
        self.dev_ws: WebSocket | None = None

    @staticmethod
    async def _assets() -> PlainTextResponse:
        _bundle = pkgutil.get_data("schorle", "assets/bundle.js")
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)

    def reflect(self, new_instance: Schorle) -> None:
        logger.debug(f"Reflecting new instance with routes: {new_instance.routes}...")
        self._instance = new_instance

    def _dynamic_handler(self, path: str) -> HTMLResponse:
        """
        Since FastAPI doesn't support dynamically changing routes, we have to
        cover them with a catch-all route and handle them ourselves.
        :param path:
        :return:
        """
        _path = f"/{path}"

        if self._instance is None:
            msg = "No instance to handle dynamic path."
            raise Exception(msg)

        page = self._instance.routes.get(_path)

        if page is None:
            return HTMLResponse(f"404 - Page not found: {_path}", status_code=404)

        return page.render_to_response(body_class=BodyWithPageAndDeveloperTools)

    async def _devtools_handler(self, ws: WebSocket) -> None:
        if self._instance is None:
            msg = "No instance to handle devtools."
            raise Exception(msg)

        await ws.accept()
        self.dev_ws = ws

        async for message in self.dev_ws.iter_json():
            logger.debug(f"Received message: {message}")

        logger.debug("Closing websocket...")
