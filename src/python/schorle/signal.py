from __future__ import annotations

from contextlib import asynccontextmanager
from functools import partial
from typing import Callable, Generic, TypeVar

from dependency_injector.providers import Factory, Singleton
from pydantic import BaseModel, PrivateAttr

T = TypeVar("T")


class Signal(BaseModel, Generic[T]):
    _value: T | None = PrivateAttr(default=None)
    _observers: list[Callable] = PrivateAttr(default_factory=list)

    def __init__(self, value: T):
        super().__init__()
        self._value = value

    async def update(self, value: T, *, skip_notify: bool = False):
        self._value = value
        if not skip_notify:
            for observer in self._observers:
                await observer()

    def partial(self, value: T):
        return partial(self.update, value)

    def __call__(self):
        return self._value

    def subscribe(self, observer):
        self._observers.append(observer)

    @classmethod
    def factory(cls, value: T | None = None) -> Callable[[], Signal[T]]:
        return Factory(cls, value)

    @asynccontextmanager
    async def ctx(self, value: T):
        previous = self._value
        await self.update(value)
        try:
            yield
        finally:
            await self.update(previous)

    @classmethod
    def shared(cls, value: T | None = None):
        return Singleton(cls, value)

    def __repr__(self):
        return f"<Signal value={self._value}>"

    def __str__(self):
        return self.__repr__()
