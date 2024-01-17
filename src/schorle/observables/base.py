from __future__ import annotations

from asyncio import Queue
from typing import AsyncIterator, Generic, TypeVar

from loguru import logger
from pydantic import BaseModel, PrivateAttr

T = TypeVar("T")


class Observable(BaseModel, Generic[T]):
    _render_queue: Queue = PrivateAttr(default_factory=Queue)
    _value: T | None = PrivateAttr()

    async def update(self, value: T):
        self._value = value
        logger.debug(f"Updating {self} with {value}")
        await self._render_queue.put(self)

    async def __aiter__(self) -> AsyncIterator[T | None]:
        while True:
            await self._render_queue.get()
            yield self._value

    def get(self):
        return self._value

    def __init__(self, value: T | None = None):
        super().__init__()
        self._value = value

    def __repr__(self):
        return f"<Observable {self.__class__} {self._value}>"

    def __str__(self):
        return f"<Observable {self.__class__} {self._value}>"


