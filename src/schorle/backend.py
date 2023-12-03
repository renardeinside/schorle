import pkgutil

from fastapi import FastAPI
from loguru import logger
from starlette.responses import PlainTextResponse
from starlette.websockets import WebSocket

from schorle.app import Schorle
from schorle.proto_gen.schorle import ElementUpdateEvent, Event
from schorle.renderer import Renderer
from schorle.signal import SIGNALS


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
                signals = SIGNALS.get()

                logger.debug(f"Signals: {signals}")
                signal = signals.get(event.click.signal_id)
                logger.debug(f"Signal: {signal}")

                effect = signal.effects.get(event.click.effect_id)

                logger.debug(f"Effect: {effect}, executing")

                await effect()

                logger.debug(f"Effect: {effect}, executed")

                for dependant in signal.dependants:
                    logger.debug(f"Dependant: {dependant}")
                    element_id = dependant.consistent_id
                    recomputed_element = await dependant()
                    recomputed_element.attrs["id"] = element_id
                    logger.debug(f"Recomputed element: {recomputed_element}")
                    logger.info(f"Sending update event for {element_id}")
                    new_element = await Renderer.render(recomputed_element)
                    logger.debug(f"New element: {new_element}")
                    update_event = Event(element_update=ElementUpdateEvent(id=element_id, payload=new_element))
                    logger.debug(f"Update event: {update_event}")
                    await ws.send_bytes(bytes(update_event))

    async def _assets(self) -> PlainTextResponse:
        _bundle = pkgutil.get_data("schorle", "assets/bundle.js")
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)

    async def index(self, path: str):
        _path = path or "/"

        if _path not in self._routes:
            return PlainTextResponse("Not found", status_code=404)

        page_object = await self._routes[_path]()
        self._rendered_pages[_path] = page_object
        response = await Renderer.render_to_response(page_object, self._theme)
        logger.info(f"Returning response: {response.body}")
        return response
