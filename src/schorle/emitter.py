import asyncio

from lxml import etree
from starlette.websockets import WebSocket

from schorle.page import Page
from schorle.utils import render_in_context


class PageEmitter:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def emit(self, ws: WebSocket) -> None:
        while True:
            try:
                await asyncio.sleep(0.0001)
                component = await self._page._render_queue.get()
                with self._page:
                    rendered = render_in_context(component, self._page)
                    await ws.send_text(etree.tostring(rendered, pretty_print=True).decode())
            except Exception as e:
                print(e)
                break
