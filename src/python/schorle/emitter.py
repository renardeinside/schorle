import asyncio

from loguru import logger
from lxml import etree
from starlette.websockets import WebSocket

from schorle.controller import RenderController
from schorle.models import Action, ServerMessage
from schorle.page import Page


class PageEmitter:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def emit(self, ws: WebSocket) -> None:
        while True:
            try:
                await asyncio.sleep(0.0001)
                renderable = await self._page.render_queue.get()

                with RenderController() as rc:
                    with self._page:
                        rendered = rc.render(renderable)
                        _html = etree.tostring(rendered, pretty_print=True).decode()
                        target = rendered.get("id")

                _msg = ServerMessage(target=target, payload=_html, action=Action.morph)
                await ws.send_bytes(_msg.encode())
            except Exception as e:
                logger.error(f"Error while emitting: {e}")
                break
