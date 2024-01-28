import asyncio

from starlette.websockets import WebSocket

from schorle.elements.base.element import Element
from schorle.elements.page import Page
from schorle.reactives.base import ReactiveBase


class PageEmitter:
    # root emitter that controls the whole page.

    def __init__(self, page: Page):
        self.page = page
        self.emitters = self.create_emitters()

    def create_emitters(self):
        emitters = []
        for element in self.page.traverse():
            if isinstance(element, Element):
                emitters.append(ElementEmitter(element))
        return emitters

    async def emit(self, ws: WebSocket):
        emitter_tasks = []
        for emitter in self.emitters:
            emitter_tasks.append(emitter.emit_to(ws, self.page))
        await asyncio.gather(*emitter_tasks)


async def attr_to_queue(attr: ReactiveBase, target: asyncio.Queue):
    # add a single reactive attribute to the queue.
    async for value in attr:
        await target.put(value)


class ElementEmitter:
    # emitter that controls a single element.

    def __init__(self, element: Element):
        self.element = element
        self.queue = asyncio.Queue()
        self.attributes_to_queue_task = asyncio.create_task(self.attributes_to_queue())

    async def attributes_to_queue(self):
        reactive_attributes = self.element.get_reactive_attributes()
        tasks = []
        for attr in reactive_attributes:
            tasks.append(attr_to_queue(attr, self.queue))
        await asyncio.gather(*tasks)

    async def emit_to(self, ws: WebSocket, page: Page):
        while True:
            await asyncio.sleep(0.0001)  # prevent blocking
            if not self.queue.empty():
                await process_queue(self.queue, page)
                # re-render the element and send the update to the client
                await ws.send_text(self.element.render())


async def process_queue(queue: asyncio.Queue, page: Page):
    # process a queue of elements that were added to the page.
    while not queue.empty():
        element = await queue.get()
        await process_queue_output(element, page)


async def process_queue_output(element, page):
    # process a single element that was added to the page.
    if isinstance(element, list):
        for _element in element:
            await process_queue_output(_element, page)
    elif isinstance(element, Element):
        element.inject_page_reference(page)
        await element.before_render()
