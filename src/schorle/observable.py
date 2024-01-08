import asyncio
from asyncio import Queue

from pydantic import BaseModel, PrivateAttr


class Subscriber:
    def __init__(self):
        self.queue: Queue = Queue()

    async def __aiter__(self):
        while True:
            await asyncio.sleep(0)  # prevent blocking
            yield await self.queue.get()


class ObservableModel(BaseModel):
    _selected_fields: list[str] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._subscribers: list[Subscriber] = []

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if not self._selected_fields or name in self._selected_fields:
            for subscriber in self._subscribers:
                subscriber.queue.put_nowait(self)

    def subscribe(self, subscriber: Subscriber):
        self._subscribers.append(subscriber)
