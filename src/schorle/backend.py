import pkgutil

from fastapi import FastAPI
from loguru import logger
from starlette.responses import PlainTextResponse
from starlette.websockets import WebSocket

from schorle.app import Schorle
from schorle.elements.base import BaseElement, OnClickElement
from schorle.page import Page
from schorle.proto_gen.schorle import ElementUpdateEvent, Event
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
            if event.click:
                logger.info(f"Received click event: {event.click}")
                _page: Page = self._rendered_pages[event.click.path]
                # find the respective element
                element: OnClickElement | None = _page.find_by_id(event.click.id)
                if not element:
                    logger.error(f"Could not find element with id {event.click.id}")
                    continue
                _signal, _func = element.on_click
                _func(_signal.value)
                # find dependants
                dependants: list[BaseElement] = _page.find_dependants_of(_signal)
                for d in dependants:
                    logger.info(f"Found dependant: {d}")
                    _rendered = Renderer.render(d)
                    logger.info(f"Rendered: {_rendered}")
                    _event = Event(element_update=ElementUpdateEvent(id=d.attrs["id"], payload=_rendered))
                    await ws.send_bytes(bytes(_event))

    async def _assets(self) -> PlainTextResponse:
        _bundle = pkgutil.get_data("schorle", "assets/bundle.js")
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)

    async def index(self, path: str):
        _path = path or "/"

        if _path not in self._routes:
            return PlainTextResponse("Not found", status_code=404)

        page_object = await self._routes[_path]()
        self._rendered_pages[_path] = page_object
        response = Renderer.render_to_response(page_object, self._theme)
        logger.info(f"Returning response: {response.body}")
        return response
