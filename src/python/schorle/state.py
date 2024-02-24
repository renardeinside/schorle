import asyncio
from typing import Callable, Generic, TypeVar

from pydantic import BaseModel, Field

from schorle.effector import EffectorProtocol, effector_listing, inject_effectors


class EffectorMixin:
    def get_effectors(self):
        return effector_listing(self)


class ReactiveModel(BaseModel, EffectorMixin, extra="allow"):
    def __init__(self, **data):
        super().__init__(**data)
        inject_effectors(self)

    @classmethod
    def factory(cls, **data):
        return Field(default_factory=lambda: cls(**data))


class ReactiveState(EffectorMixin):
    def __init__(self):
        inject_effectors(self)


def effector(func: Callable) -> EffectorProtocol:
    if not asyncio.iscoroutinefunction(func):
        msg = f"Effector must be a coroutine function. {func.__name__} is not a coroutine function"
        raise ValueError(msg)
    func.is_emitter = True  # type: ignore[attr-defined]
    return func  # type: ignore[return-value]


T = TypeVar("T")


class Reactive(ReactiveModel, Generic[T]):
    value: T | None = None

    def __init__(self, **data):
        if "value" not in data:
            data["value"] = None
        super().__init__(**data)

    @effector
    async def set(self, value: T | None):
        self.value = value
