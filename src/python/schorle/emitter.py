import asyncio

from loguru import logger
from lxml import etree
from starlette.websockets import WebSocket

from schorle.component import Component
from schorle.page import Page
from schorle.types import LXMLElement
from schorle.utils import render_in_context


class PageEmitter:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def emit(self, ws: WebSocket) -> None:
        while True:
            try:
                await asyncio.sleep(0.0001)
                renderable = await self._page._render_queue.get()
                target = None
                if isinstance(renderable, LXMLElement):
                    _html = etree.tostring(renderable, pretty_print=True).decode()
                    target = renderable.get("id")
                elif isinstance(renderable, Component):
                    with self._page:
                        rendered = render_in_context(renderable, self._page)
                        _html = etree.tostring(rendered, pretty_print=True).decode()
                        target = rendered.get("id")
                else:
                    msg = f"Unknown renderable: {renderable}"
                    raise ValueError(msg)

                _msg = {
                    "target": target,
                    "html": _html,
                }
                await ws.send_json(_msg)
            except Exception as e:
                logger.error(f"Error while emitting: {e}")
                break
