import asyncio
import pkgutil

from fastapi import FastAPI
from loguru import logger
from lxml.etree import tostring
from starlette.responses import PlainTextResponse
from starlette.websockets import WebSocket

from schorle.app import Schorle
from schorle.elements.base import BaseElement
from schorle.handlers import ClickHandler
from schorle.proto_gen.schorle import Event, FullUpdateEvent
from schorle.renderer import Renderer


class BackendApp:
    def __init__(self) -> None:
        self.app = FastAPI()
        self.app.get("/_schorle/assets/bundle.js")(self._assets)
        self.app.websocket("/_schorle/ws")(self.websocket_handler)
        self.app.get("/{path:path}")(self.index)
        self.ws: WebSocket | None = None
        self._routes = {}
        self._rendered_pages = {}
        self._theme = None

    async def reflect(self, instance: Schorle):
        await self.reflect_routes(instance)
        await self.reflect_theme(instance)

    async def reflect_routes(self, instance: Schorle):
        logger.info("Reflecting routes")
        self._routes = {}
        for path, func in instance.routes.items():
            logger.info(f"Reflecting route {path} -> {func} with id {id(func)}")
            self._routes[path] = func

    async def reflect_theme(self, instance: Schorle):
        logger.info("Reflecting theme")
        self._theme = instance.theme

    async def websocket_handler(self, ws: WebSocket):
        await ws.accept()
        self.ws = ws
        while True:
            raw_event = await ws.receive_bytes()
            event = Event().parse(raw_event)
            logger.info(f"Received event: {event}")
            if event.click.target_id:
                logger.info(f"Received click event: {event.click}")
                await ClickHandler.handle(event.click)

    async def _assets(self) -> PlainTextResponse:
        _bundle = pkgutil.get_data("schorle", "assets/bundle.js")
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)

    async def index(self, path: str):
        _path = path or "/"

        if _path not in self._routes:
            return PlainTextResponse("Not found", status_code=404)

        page_object = await self._routes[_path]()
        self._rendered_pages[_path] = page_object

        async def _observer(element: BaseElement):
            while not self.ws:
                await asyncio.sleep(0.1)
                logger.warning(f"Observer called for element: {element} but no websocket is available")

            logger.info(f"Observer called for element: {element}")
            rendered = await Renderer.render(element)
            _prepared = tostring(rendered, pretty_print=True, doctype="<!DOCTYPE html>").decode("utf-8")

            event = Event(full_update=FullUpdateEvent(id=element.attrs["id"], html=_prepared))

            logger.info(f"Sending event: {event}")
            await self.ws.send_bytes(bytes(event))

        response = await Renderer.render_to_response(page_object, self._theme, _observer)
        return response
