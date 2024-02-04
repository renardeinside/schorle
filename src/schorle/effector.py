import asyncio
from asyncio import Protocol
from functools import wraps
from inspect import ismethod

from pydantic import BaseModel


class Effector:
    def __init__(self, bounded_method):
        self.bounded_method = bounded_method
        self.subscribers = []
        self.trigger_tasks = []

    async def __call__(self, *args, **kwargs):
        await self.bounded_method(*args, **kwargs)
        tasks = [subscriber(self.bounded_method.__self__) for subscriber in self.subscribers]
        await asyncio.gather(*tasks)

    async def subscribe(self, callback, *, trigger: bool = True):
        self.subscribers.append(callback)
        if trigger:
            trigger = asyncio.create_task(callback(self.bounded_method.__self__))
            self.trigger_tasks.append(trigger)


class EffectorProtocol(Protocol):
    async def subscribe(self, callback, *, trigger: bool = True):
        ...

    async def __call__(self, *args, **kwargs):
        ...


def create_emitter(func) -> EffectorProtocol:
    _emitter_instance = Effector(func)

    async def _wrapper(*args, **kwargs):
        await _emitter_instance(*args, **kwargs)

    wrapper: EffectorProtocol = wraps(func)(_wrapper)
    wrapper.subscribe = _emitter_instance.subscribe
    return wrapper


def effector(func) -> EffectorProtocol:
    if not asyncio.iscoroutinefunction(func):
        raise ValueError("emitter can only be used on async functions")
    func.is_emitter = True
    return func


def inject_effectors(_object: object):
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
