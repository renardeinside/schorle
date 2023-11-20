import base64
import hashlib
import pkgutil

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, PlainTextResponse
from loguru import logger
from vdom import VDOM, div
from vdom.core import create_component

html = create_component("html")
script = create_component("script")
head = create_component("head")
meta = create_component("meta")
body = create_component("body")
title = create_component("title")
link = create_component("link")


class Page:
    def __init__(self, *children: VDOM):
        self.children = children

    def __repr__(self) -> str:
        return f"Page({[c.to_html() for c in self.children]})"


def _get_integrity_hash(bundle):
    _b64_bytes = base64.b64encode(hashlib.sha384(bundle).digest())
    sha = "sha384-" + _b64_bytes.decode("utf-8")
    return sha


_bundle = pkgutil.get_data("schorle", "assets/bundle.js")
_integrity_hash = _get_integrity_hash(_bundle)


def _prepared_head() -> VDOM:
    return head(
        meta(charset="utf-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1"),
        title("Schorle"),
        script(src="https://cdn.tailwindcss.com"),
        script(src="/_schorle/assets/bundle.js", integrity=_integrity_hash, crossorigin="anonymous"),
        link(href="https://cdn.jsdelivr.net/npm/daisyui@4.4.2/dist/full.min.css", rel="stylesheet", type="text/css"),
    )


def prepare_response(func):
    async def wrapper() -> HTMLResponse:
        _page = await func()
        return HTMLResponse(
            html(_prepared_head(), body(div(
                *_page.children,
                attributes={"id": "schorle-app"}
            ))).to_html(),
            status_code=200,
        )

    return wrapper


class Schorle:
    def __init__(self) -> None:
        self.routes = {}

    def route(self, path: str):
        """Decorator to register a function as a route handler."""

        def decorator(func):
            self.routes[path] = func
            return func

        return decorator


class BackendApp:
    def __init__(self) -> None:
        self.app = FastAPI()
        self.app.get("/_schorle/assets/bundle.js")(self._assets)
        self.app.websocket("/_schorle/ws")(self.websocket_handler)
        self.app.get("/{path:path}")(self.index)
        self.ws = None
        self._routes = {}

    async def reflect_routes(self, instance):
        logger.info("Reflecting routes")
        self._routes = {}
        for path, func in instance.routes.items():
            logger.info(f"Reflecting route {path} -> {func} with id {id(func)}")
            self._routes[path] = prepare_response(func)

    async def websocket_handler(self, ws: WebSocket):
        await ws.accept()
        self.ws = ws
        while True:
            _ = await ws.receive_json()

    async def _assets(self) -> PlainTextResponse:
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)

    async def index(self, path: str):
        _path = path or "/"

        if _path not in self._routes:
            return PlainTextResponse("Not found", status_code=404)

        return await self._routes[_path]()
