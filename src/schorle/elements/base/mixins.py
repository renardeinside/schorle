from __future__ import annotations

from copy import deepcopy
from functools import partial

from pydantic import BaseModel
from pydantic.fields import ComputedFieldInfo, Field, FieldInfo


class AttrsMixin(BaseModel):
    """
    Handles the attributes of the element.
    Attributes should be defined as fields with the `Attribute` annotation.
    """

    @staticmethod
    def __define_name(k, v):
        return v.json_schema_extra.get("attribute_name") if v.json_schema_extra.get("attribute_name") else k

    def get_element_attributes(self) -> dict[str, str]:
        _without_page_ref = {
            k: v
            for k, v in self.model_fields.items()
            if v.json_schema_extra and not v.json_schema_extra.get("page_reference")
        }
        model_fields = deepcopy(_without_page_ref)
        computed_fields = {k: v for k, v in deepcopy(self.model_computed_fields).items() if k != "attrs"}
        all_fields: dict[str, FieldInfo | ComputedFieldInfo] = {**model_fields, **computed_fields}
        _attrs = {}
        for field_name, field_info in all_fields.items():
            if field_info.json_schema_extra and field_info.json_schema_extra.get("attribute"):  # type: ignore
                _attrs[self.__define_name(field_name, field_info)] = self.__getattribute__(field_name)
        return _attrs


class FactoryMixin:
    @classmethod
    def factory(cls, *args, **kwargs) -> FieldInfo:
        return Field(default_factory=partial(cls, *args, **kwargs), json_schema_extra={"class_meta": cls})
