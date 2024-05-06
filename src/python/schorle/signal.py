from __future__ import annotations

from contextlib import asynccontextmanager
from functools import partial
from typing import Callable, Generic, TypeVar

from pydantic import BaseModel, Field, PrivateAttr

T = TypeVar("T")


class Signal(BaseModel, Generic[T]):
    _value: T | None = PrivateAttr(default=None)
    _observers: list[Callable] = PrivateAttr(default_factory=list)

    def __init__(self, value: T):
        super().__init__()
        self._value = value

    async def set(self, value: T, *, skip_notify: bool = False):
        self._value = value
        if not skip_notify:
            for observer in self._observers:
                await observer()

    def lazy(self, value: T):
        return partial(self.set, value)

    @property
    def val(self) -> T:
        return self._value

    def subscribe(self, observer):
        self._observers.append(observer)

    @classmethod
    def factory(cls, value: T | None = None) -> Callable[[], Signal[T]]:
        return partial(cls, value)

    @asynccontextmanager
    async def ctx(self, value: T):
        previous = self._value
        await self.set(value)
        try:
            yield
        finally:
            await self.set(previous)

    @classmethod
    def field(cls, default_value: T | None = None) -> Field:
        return Field(default_factory=cls.factory(default_value))
