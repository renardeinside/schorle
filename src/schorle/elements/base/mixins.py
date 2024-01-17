from __future__ import annotations

import inspect
from copy import deepcopy
from enum import Enum
from inspect import ismethod
from types import MethodType
from typing import Callable, Iterator, get_origin

from loguru import logger
from pydantic import BaseModel
from pydantic.fields import ComputedFieldInfo, FieldInfo

from schorle.state import Depends, Uses, Wired


class Bootstrap(str, Enum):
    ON_LOAD = "on_load"
    BEFORE_RENDER = "before_render"


class AttrsMixin(BaseModel):
    """
    Handles the attributes of the element.
    Attributes should be defined as fields with the `Attribute` annotation.
    """

    @staticmethod
    def __define_name(k, v):
        return v.json_schema_extra.get("attribute_name") if v.json_schema_extra.get("attribute_name") else k

    def get_element_attributes(self) -> dict[str, str]:
        model_fields = deepcopy(self.model_fields)
        computed_fields = {k: v for k, v in deepcopy(self.model_computed_fields).items() if k != "attrs"}
        all_fields: dict[str, FieldInfo | ComputedFieldInfo] = {**model_fields, **computed_fields}
        _attrs = {}
        for field_name, field_info in all_fields.items():
            if field_info.json_schema_extra and field_info.json_schema_extra.get("attribute"):  # type: ignore
                _attrs[self.__define_name(field_name, field_info)] = self.__getattribute__(field_name)
        return _attrs


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
