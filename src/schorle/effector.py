from asyncio import Protocol
from collections.abc import Iterable
from dataclasses import dataclass
from functools import wraps
from inspect import ismethod
from types import MethodType
from typing import Callable

from pydantic import BaseModel


class Effector:
    def __init__(self, bounded_method: MethodType):
        self.bounded_method = bounded_method
        self.subscribers = []

    def __call__(self, *args, **kwargs):
        self.bounded_method(*args[1:], **kwargs)
        for subscriber in self.subscribers:
            subscriber()

    def subscribe(self, callback):
        self.subscribers.append(callback)


class EffectorProtocol(Protocol):
    async def subscribe(self, callback, *, trigger: bool = True):
        ...

    async def __call__(self, *args, **kwargs):
        ...


def create_emitter(func: MethodType) -> EffectorProtocol:
    _emitter_instance = Effector(func)

    def _wrapper(*args, **kwargs):
        _emitter_instance(*args, **kwargs)

    wrapper: EffectorProtocol = wraps(func)(_wrapper)
    wrapper.subscribe = _emitter_instance.subscribe
    return wrapper


def effector(func: Callable) -> EffectorProtocol:
    func.is_emitter = True
    return func  # type: ignore


@dataclass
class EffectorInfo:
    method: MethodType
    attr: str


def effector_listing(_object: object) -> Iterable[EffectorInfo]:
    if isinstance(_object, BaseModel) and not _object.model_config.get("extra", None) == "allow":
        raise ValueError("Pydantic models must be declared with extra='allow' to use inject_emitters")
    for attr in dir(_object):
        if attr not in ["__fields__", "__fields_set__", "__signature__"] and (
            attr not in _object.model_computed_fields.keys() if isinstance(_object, BaseModel) else True
        ):
            if callable(getattr(_object, attr)) and ismethod(getattr(_object, attr)):
                _method: MethodType = getattr(_object, attr)
                if hasattr(_method.__func__, "is_emitter"):
                    yield EffectorInfo(_method, attr)


def inject_effectors(_object: object):
    for effector_info in effector_listing(_object):
        emitter_func = create_emitter(effector_info.method)
        emitter_method = MethodType(emitter_func, _object)
        setattr(_object, effector_info.attr, emitter_method)
