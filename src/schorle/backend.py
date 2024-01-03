import asyncio
import pkgutil
from asyncio import CancelledError

from fastapi import FastAPI
from loguru import logger
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.websockets import WebSocket

from schorle.app import Schorle
from schorle.elements.base import Element
from schorle.elements.html import BodyWithPageAndDeveloperTools
from schorle.models import HtmxMessage


class BackendApp:
    def __init__(self, app: FastAPI | None = None) -> None:
        self.app = FastAPI() if app is None else app
        self.app.get("/_schorle/assets/{file_name}")(self._assets)
        self.app.get("/{path:path}")(self._dynamic_handler)
        self.app.websocket("/_schorle/devtools")(self._devtools_handler)
        self.app.websocket("/_schorle/events")(self._events_handler)
        self._instance: Schorle | None = None
        self.dev_ws: WebSocket | None = None
        self.events_ws: WebSocket | None = None

    @staticmethod
    async def _assets(file_name: str) -> PlainTextResponse:
        _bundle = pkgutil.get_data("schorle", f"assets/{file_name}")
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)

    def reflect(self, new_instance: Schorle) -> None:
        logger.debug(f"Reflecting new instance with routes: {new_instance.routes}...")
        self._instance = new_instance

    async def subscriber(self, element: Element) -> None:
        logger.debug(f"Event subscription called for {element.element_id}")

        while not self.events_ws:
            await asyncio.sleep(0.1)
            logger.debug("Waiting for events websocket to be ready...")

        logger.debug(f"Sending update for {element.element_id} to events websocket...")
        new_render = element.render()
        await self.events_ws.send_text(new_render)

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

        page.set_subscriber(self.subscriber)

        return page.render_to_response(body_class=BodyWithPageAndDeveloperTools)

    async def _devtools_handler(self, ws: WebSocket) -> None:
        if self._instance is None:
            msg = "No instance to handle devtools."
            raise Exception(msg)

        await ws.accept()
        self.dev_ws = ws

        try:
            async for message in self.dev_ws.iter_json():
                logger.debug(f"Received message: {message}")
        except CancelledError:
            logger.debug("Keyboard interrupt received, closing dev websocket...")
            await self.dev_ws.close()

    async def _events_handler(self, ws: WebSocket) -> None:
        if self._instance is None:
            msg = "No instance to handle events"
            raise Exception(msg)

        await ws.accept()
        self.events_ws = ws

        try:
            async for raw_message in self.events_ws.iter_json():
                logger.debug(f"Received message in events socket: {raw_message}")
                message = HtmxMessage(**raw_message)
                _path = self.events_ws.query_params.get("path")
                page = self._instance.routes.get(_path)
                if page is None:
                    logger.warning(f"Page not found: {_path}")

                _button = page.find_by_id(message.headers.trigger)
                if _button is None:
                    logger.warning(f"Button not found: {message.headers.trigger}")

                if _button.on_click is not None:
                    logger.debug(f"Calling on_click handlers for button {_button.element_id}")
                    await _button.on_click()
                else:
                    logger.warning(f"Button {_button} has no on_click handler")

        except CancelledError:
            logger.debug("Keyboard interrupt received, closing events websocket...")
            await self.events_ws.close()
