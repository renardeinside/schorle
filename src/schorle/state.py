from __future__ import annotations

import inspect
from abc import ABC
from typing import Any, Generic, TypeVar, get_origin

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass  # type: ignore
from pydantic.fields import FieldInfo

T = TypeVar("T")


class Provide(Generic[T]):
    ...


class BaseMeta(ModelMetaclass):
    def __getattr__(self, item: str) -> Any:
        if item.startswith("__") or self is State:
            # this handles standard getattr calls
            return getattr(super(), item)
        else:
            # this handles the XYZ[SubclassedState.attribute] calls
            field: FieldInfo = self.model_fields[item]
            field.json_schema_extra = {"name": item}
            return field


class State(BaseModel, ABC, metaclass=BaseMeta):
    pass


def inject_state(state, func):
    signature = inspect.signature(func)
    parameters = signature.parameters

    def wrapper():
        new_kwargs = {}

        for name, parameter in parameters.items():
            default = parameter.default
            if get_origin(default) is Provide:
                for arg in default.__args__:
                    if isinstance(arg, FieldInfo) and "name" in arg.json_schema_extra:
                        new_kwargs[name] = getattr(state, arg.json_schema_extra["name"])

        return func(**new_kwargs)

    return wrapper


def is_injectable(prop):
    if callable(prop):
        signature = inspect.signature(prop)
        parameters = signature.parameters

        for _, parameter in parameters.items():
            if get_origin(parameter.default) is Provide:
                return True
        return False
    else:
        return False
