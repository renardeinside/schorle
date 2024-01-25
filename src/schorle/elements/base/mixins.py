from __future__ import annotations

from copy import deepcopy
from enum import Enum

from pydantic import BaseModel
from pydantic.fields import ComputedFieldInfo, FieldInfo


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
