import asyncio
from typing import Callable, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from schorle.effector import EffectorProtocol, effector_listing, inject_effectors


class EffectorMixin:
    def get_effectors(self):
        return effector_listing(self)


class ReactiveModel(BaseModel, EffectorMixin, extra="allow"):
    reactive_id: UUID = Field(default_factory=lambda: uuid4())
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data):
        super().__init__(**data)
        inject_effectors(self)

    @classmethod
    def factory(cls, **data):
        return Field(default_factory=lambda: cls(**data))

    def __hash__(self):
        return hash(self.reactive_id)


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


R = TypeVar("R")


class Ref(Generic[R]):

    def __init__(self, current: R | None = None):
        self.current = current

    def set(self, value: R):
        self.current = value

    def __repr__(self):
        return f"<Ref({self.current})/>"

    def __str__(self):
        return self.__repr__()
