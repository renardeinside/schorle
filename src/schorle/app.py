import asyncio
import json
import pkgutil
from functools import partial
from typing import Callable

from fastapi import FastAPI
from loguru import logger
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.websockets import WebSocket

from schorle.elements.base import Subscriber
from schorle.elements.html import BodyWithPage, EventHandler, Html, MorphWrapper
from schorle.elements.page import Page
from schorle.models import HtmxMessage
from schorle.theme import Theme


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK) -> None:
        self._pages: dict[str, Page] = {}
        self.backend = FastAPI()
        self.backend.get("/_schorle/assets/{file_name}")(self._assets)
        self.backend.add_websocket_route("/_schorle/events", partial(EventsEndpoint, pages=self._pages))
        self.theme: Theme = theme

    def get(self, path: str):
        def decorator(func: Callable[..., Page]):
            async def _route_wrapper() -> HTMLResponse:
                _page = func()
                return await self.render_to_response(page=_page)

            self.backend.get(path, response_class=HTMLResponse)(_route_wrapper)
            return func

        return decorator

    async def render_to_response(self, page: Page) -> HTMLResponse:
        logger.info(f"Rendering page: {page}...")
        on_load_tasks = page.get_all_on_load_tasks()

        if on_load_tasks:
            logger.info(f"Running on_loads: {on_load_tasks}")
            try:
                await asyncio.gather(*on_load_tasks)
            except asyncio.CancelledError:
                logger.info("Bootstrapping cancelled.")
                for task in on_load_tasks:
                    task.cancel()

        handler = EventHandler(content=page)
        body = BodyWithPage(wrapper=MorphWrapper(handler=handler))
        logger.debug(f"Rendering page: {page} with theme: {self.theme}...")
        html = Html(body=body, **{"data-theme": self.theme})
        response = HTMLResponse(html.render(), status_code=200)
        logger.info(f"Adding page to cache with token: {html.head.csrf_meta.content}")
        self._pages[html.head.csrf_meta.content] = page
        logger.debug("Page rendered.")
        return response

    @staticmethod
    async def _assets(file_name: str) -> PlainTextResponse:
        _bundle = pkgutil.get_data("schorle", f"assets/{file_name}")
        return PlainTextResponse(_bundle.decode("utf-8"), status_code=200)


class EventsEndpoint(WebSocketEndpoint):
    encoding = "text"

    def __init__(self, scope, receive, send, pages: dict[str, Page]) -> None:
        super().__init__(scope, receive, send)
        self._page_binding_task = None
        self._page_updates_task = None
        self._page = None
        self._pages = pages

    async def _page_updates_emitter(self, ws: WebSocket) -> None:
        subscriber = Subscriber()
        self._page.subscribe_all_elements(subscriber)

        logger.info("Starting the page updates emitter...")
        async for element in subscriber:
            rendered = element.render()
            logger.info(f"Sending page updates to client: {rendered}")
            await ws.send_text(rendered)

    async def _binding_updates_emitter(self) -> None:
        binding_tasks = self._page.get_all_binding_tasks()
        await asyncio.gather(*binding_tasks)

    async def on_connect(self, websocket: WebSocket) -> None:
        token = websocket.query_params.get("token")
        page = self._pages.get(token)
        if not page:
            logger.error(f"No page found for token: {token}")
            await websocket.close()
            return

        await websocket.accept()
        self._page = page
        self._page_updates_task = asyncio.create_task(self._page_updates_emitter(websocket))
        self._page_binding_task = asyncio.create_task(self._binding_updates_emitter())
        logger.info("Events connected.")

    async def on_receive(self, _: WebSocket, data: str) -> None:
        logger.warning(f"Events received message: {data}")
        message = HtmxMessage(**json.loads(data))

        _element = self._page.find_by_id(message.headers.trigger)

        if _element is None:
            logger.error(f"No element found for trigger: {message.headers.trigger}")
            return

        if _element.on_click is not None:
            logger.info(f"Calling on_click handlers for element {_element.element_id}")
            await _element.on_click()

    async def on_disconnect(self, _: WebSocket, close_code: int) -> None:
        logger.info(f"Events disconnected with code: {close_code}")
        for task in (self._page_updates_task, self._page_binding_task):
            if task is not None:
                task.cancel()
