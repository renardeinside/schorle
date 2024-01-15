from __future__ import annotations

import inspect
from enum import Enum
from inspect import ismethod
from types import MethodType
from typing import Callable, Iterator, get_origin

from loguru import logger
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from schorle.elements.attribute import Attribute
from schorle.state import Depends, Uses, Wired


class Bootstrap(str, Enum):
    ON_LOAD = "on_load"
    BEFORE_RENDER = "before_render"


class AttrsMixin(BaseModel):
    """
    Handles the attributes of the element.
    Attributes should be defined as fields with the `Attribute` annotation.
    """

    @property
    def attrs(self):
        return {
            v.serialization_alias if v.serialization_alias else k: getattr(self, k)
            for k, v in self.model_fields.items()
            if v.json_schema_extra and v.json_schema_extra.get("attribute")
        }


class SendMixin(BaseModel):
    ws_send: str = Attribute(default="", alias="ws-send")


class InjectableMixin:
    """
    Handles the injection of state into the element.
    """

    def injectable_methods(self) -> Iterator[MethodType]:
        for attr in dir(self):
            if attr not in ["__fields__", "__fields_set__", "__signature__"] and ismethod(getattr(self, attr)):
                method = getattr(self, attr)
                injectable_params = [
                    param
                    for param in inspect.signature(method).parameters.values()
                    if get_origin(param.default) in [Uses, Depends]
                ]
                if injectable_params:
                    yield method

    def injected_methods(self) -> Iterator[MethodType]:
        for attr in dir(self):
            if (
                attr not in ["__fields__", "__fields_set__", "__signature__"]
                and callable(getattr(self, attr))
                and getattr(getattr(self, attr), "injected", False)
            ):
                yield getattr(self, attr)

    def _injectable_params(self, method: Callable) -> Iterator[tuple[str, Wired, FieldInfo]]:
        parameters = inspect.signature(method).parameters
        for name, parameter in parameters.items():
            if get_origin(parameter.default) in [Uses, Depends]:
                yield name, get_origin(parameter.default), parameter.default.__args__[0]

    def add_injection_metadata(self):
        for method in self.injectable_methods():
            for _, wired, field_info in self._injectable_params(method):
                if wired is Uses:
                    logger.debug(f"Adding {method} to uses of {field_info.json_schema_extra['name']}")
                elif wired is Depends:
                    logger.debug(f"Adding {method} to depends of {field_info.json_schema_extra['name']}")
                    field_info.json_schema_extra["depends"].append(method)
