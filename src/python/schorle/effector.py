import asyncio
from asyncio import Protocol
from collections.abc import Iterable
from dataclasses import dataclass
from functools import wraps
from inspect import ismethod
from types import MethodType
from typing import Callable

from loguru import logger
from pydantic import BaseModel


class Effector:
    def __init__(self, bounded_method: MethodType):
        self.pre_actions: list[Callable] = []
        self.bounded_method = bounded_method
        self.subscribers: list[Callable] = []

    async def __call__(self, *args, **kwargs):
        _tasks = [asyncio.create_task(_pre_action()) for _pre_action in self.pre_actions]
        await asyncio.gather(*_tasks)

        if asyncio.iscoroutinefunction(self.bounded_method):
            logger.debug(f"Calling {self.bounded_method.__name__} as a coroutine")
            _cut_args = args[1:]
            logger.debug(f"Args: {_cut_args}, kwargs: {kwargs}")
            await self.bounded_method(*_cut_args)
        else:
            self.bounded_method(*args[1:], **kwargs)

        for subscriber in self.subscribers:
            await subscriber()

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def prepend(self, _pre_action):
        self.pre_actions.append(_pre_action)


class EffectorProtocol(Protocol):
    def subscribe(self, callback, *, trigger: bool = True): ...

    async def __call__(self, *args, **kwargs): ...

    def prepend(self, _pre_action): ...


def create_emitter(func: MethodType) -> EffectorProtocol:
    _emitter_instance = Effector(func)

    async def _wrapper(*args, **kwargs):
        await _emitter_instance(*args, **kwargs)

    wrapper: EffectorProtocol = wraps(func)(_wrapper)  # type: ignore[assignment]
    wrapper.subscribe = _emitter_instance.subscribe  # type: ignore[method-assign, assignment]
    wrapper.prepend = _emitter_instance.prepend  # type: ignore[method-assign, assignment]
    return wrapper


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
