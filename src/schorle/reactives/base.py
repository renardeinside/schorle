from __future__ import annotations

from asyncio import Queue
from collections.abc import AsyncIterator
from typing import Generic, TypeVar

from loguru import logger
from pydantic import BaseModel, PrivateAttr

from schorle.elements.base.mixins import FactoryMixin

T = TypeVar("T")


class ReactiveBase(BaseModel, Generic[T], FactoryMixin):
    _render_queue: Queue = PrivateAttr(default_factory=Queue)
    _value: T | None = PrivateAttr()

    async def update(self, value: T | None, *, skip_render: bool = False):
        self._value = value
        logger.debug(f"Updating {self} with {value}")
        if not skip_render:
            await self._render_queue.put(self)
        else:
            logger.debug(f"Skipping render for {self}")

    async def __aiter__(self) -> AsyncIterator[T | None]:
        while True:
            await self._render_queue.get()
            yield self._value

    def get(self) -> T | None:
        return self._value

    def __init__(self, value: T | None = None):
        super().__init__()
        self._value = value

    def __repr__(self):
        return f"<{self.__class__.__name__} {self._value}>"

    def __str__(self):
        return f"<{self.__class__.__name__} {self._value}>"
