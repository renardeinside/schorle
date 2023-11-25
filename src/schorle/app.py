import base64
import hashlib
import pkgutil

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, PlainTextResponse
from loguru import logger
from lxml.etree import tostring

from schorle.html import (
    head,
    html,
    link,
    meta,
    script,
    title,
    body,
    Page, Renderer, OnClickElement, BaseElement
)
from schorle.proto_gen.schorle import Event, ElementUpdateEvent
from schorle.signal import Signal


def _get_integrity_hash(bundle):
    _b64_bytes = base64.b64encode(hashlib.sha384(bundle).digest())
    sha = "sha384-" + _b64_bytes.decode("utf-8")
    return sha


# _bundle = pkgutil.get_data("schorle", "assets/bundle.js")
# _integrity_hash = _get_integrity_hash(_bundle)


def _prepared_head():
    return head(
        meta(charset="utf-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1"),
        title("Schorle"),
        script(src="https://cdn.tailwindcss.com"),
        script(src="/_schorle/assets/bundle.js", crossorigin="anonymous"),
        link(href="https://cdn.jsdelivr.net/npm/daisyui@4.4.2/dist/full.min.css", rel="stylesheet", type="text/css"),
    )


def page_to_response(page: Page) -> HTMLResponse:
    _prepared = tostring(
        Renderer.render(
            html(
                _prepared_head(),
                body(page),
            )
        ),
        pretty_print=True,
        doctype="<!DOCTYPE html>",
    ).decode("utf-8")

    return HTMLResponse(
        _prepared,
        status_code=200,
    )


class Schorle:
    def __init__(self) -> None:
        self.routes = {}

    def route(self, path: str):
        """Decorator to register a function as a route handler."""

        def decorator(func):
            self.routes[path] = func
            return func

        return decorator

    def signal(self, init_value) -> Signal:
        return Signal(init_value)


class BackendApp:
    def __init__(self) -> None:
        self.app = FastAPI()
        self.app.get("/_schorle/assets/bundle.js")(self._assets)
        self.app.websocket("/_schorle/ws")(self.websocket_handler)
        self.app.get("/{path:path}")(self.index)
        self.ws: WebSocket | None = None
        self._routes = {}
        self._rendered_pages = {}

    async def reflect_routes(self, instance):
        logger.info("Reflecting routes")
        self._routes = {}
        for path, func in instance.routes.items():
            logger.info(f"Reflecting route {path} -> {func} with id {id(func)}")
            self._routes[path] = func

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
                element: OnClickElement = _page.find_by_id(event.click.id)
                _signal, _func = element.on_click
                _func(_signal.value)
                # find dependants
                dependants: list[BaseElement] = _page.find_dependants_of(_signal)
                for d in dependants:
                    logger.info(f"Found dependant: {d.element}")
                    _rendered = tostring(Renderer.render(d)).decode("utf-8")
                    logger.info(f"Rendered: {_rendered}")
                    _event = Event(
                        element_update=ElementUpdateEvent(
                            id=d.element.attrib["id"],
                            payload=_rendered
                        )
                    )
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
        response = page_to_response(page_object)
        logger.info(f"Returning response: {response.body}")
        return response
