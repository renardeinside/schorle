import asyncio
from asyncio import Protocol
from functools import wraps
from inspect import ismethod

from pydantic import BaseModel


class Emitter:
    def __init__(self, func):
        self.func = func
        self.subscribers = []

    async def __call__(self, *args, **kwargs):
        await self.func(*args, **kwargs)
        tasks = [subscriber(self.func.__self__) for subscriber in self.subscribers]
        await asyncio.gather(*tasks)

    def subscribe(self, callback):
        self.subscribers.append(callback)


class EmitterProtocol(Protocol):
    def subscribe(self, callback):
        ...

    async def __call__(self, *args, **kwargs):
        ...


def create_emitter(func) -> EmitterProtocol:
    _emitter_instance = Emitter(func)

    async def _wrapper(*args, **kwargs):
        await _emitter_instance(*args, **kwargs)

    wrapper: EmitterProtocol = wraps(func)(_wrapper)
    wrapper.subscribe = _emitter_instance.subscribe
    return wrapper


def emitter(func) -> EmitterProtocol:
    if not asyncio.iscoroutinefunction(func):
        raise ValueError("emitter can only be used on async functions")
    func.is_emitter = True
    return func


def inject_emitters(_object: object):
    if isinstance(_object, BaseModel) and not _object.model_config.get("extra", None) == "allow":
        raise ValueError("Pydantic models must be declared with extra='allow' to use inject_emitters")
    for attr in dir(_object):
        if attr not in ["__fields__", "__fields_set__", "__signature__"] and (
            attr not in _object.model_computed_fields.keys() if isinstance(_object, BaseModel) else True
        ):
            if callable(getattr(_object, attr)) and ismethod(getattr(_object, attr)):
                _method = getattr(_object, attr)
                if hasattr(_method, "is_emitter"):
                    wrapped_method = create_emitter(_method)
                    setattr(_object, attr, wrapped_method)
