from __future__ import annotations

import inspect
from abc import ABC
from types import MethodType
from typing import Any, Generic, TypeVar, get_origin

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass  # type: ignore
from pydantic.fields import FieldInfo

T = TypeVar("T")


class Wired(Generic[T]):
    ...


class Uses(Wired[T]):
    ...


class Depends(Wired[T]):
    ...


class BaseMeta(ModelMetaclass):
    def __getattr__(self, item: str) -> Any:
        if item.startswith("__") or self is State:
            # this handles standard getattr calls
            return getattr(super(), item)
        else:
            # this handles the XYZ[SubclassedState.attribute] calls
            field: FieldInfo = self.model_fields[item]
            if not field.json_schema_extra:
                field.json_schema_extra = {"name": item, "depends": [], "uses": []}
            return field


class State(BaseModel, ABC, metaclass=BaseMeta):
    pass


def get_injected_method(method: MethodType, state: State):
    """
    Injects the state into the method.
    :param method:
    :param state:
    :return:
    """

    async def _injector():
        parameters = inspect.signature(method).parameters
        new_kwargs = {}
        dependants = []
        for name, parameter in parameters.items():
            origin = get_origin(parameter.default)
            if origin in [Uses, Depends]:
                field_info = parameter.default.__args__[0]
                value = getattr(state, field_info.json_schema_extra["name"])
                new_kwargs[name] = value
                if "depends" in field_info.json_schema_extra and origin is Uses:
                    dependants.extend(field_info.json_schema_extra["depends"])

        # if method has no dependants, call it
        if not dependants:
            if inspect.iscoroutinefunction(method):
                return await method(**new_kwargs)
            else:
                return method(**new_kwargs)
        else:
            # if method has dependants, wrap it in a function that calls the dependants last
            async def _wrapper():
                await method(**new_kwargs)
                for dependant in dependants:
                    _injected = getattr(dependant.__self__, dependant.__name__)
                    if inspect.iscoroutinefunction(_injected):
                        await _injected()
                    else:
                        _injected()

            return await _wrapper()

    return _injector


def inject_into_method(state: State, original_method: MethodType):
    injected_method = get_injected_method(original_method, state)
    injected_method.injected = True
    injected_method.trigger = getattr(original_method, "trigger", None)
    injected_method.before_load = getattr(original_method, "before_load", None)
    setattr(original_method.__self__, original_method.__name__, injected_method)
