from __future__ import annotations

from typing import Any, Callable, TypeVar

from lxml.etree import _Element as LxmlElement
from pydantic import PrivateAttr, computed_field

from schorle.elements.attribute import Attribute
from schorle.elements.base.base import BaseElement
from schorle.reactives.base import ReactiveBase
from schorle.reactives.classes import Classes


class Element(BaseElement):
    _base_classes: Classes = PrivateAttr(default_factory=Classes)
    classes: Classes = Classes()
    role: str | None = Attribute(default=None)
    swap: str = Attribute(default="morph", alias="hx-swap-oob")

    def __init__(self, **data):
        super().__init__(**data)
        if self.element_id is None:
            self.element_id = (
                f"schorle-{self.tag.value.lower()}-{id(self)}" if self.element_id is None else self.element_id
            )

    @computed_field(json_schema_extra={"attribute": True, "attribute_name": "hx-trigger"})  # type: ignore
    @property
    def hx_trigger(self) -> str | None:
        return ",".join(list(self.reactive_methods.keys())) if len(self.reactive_methods) > 0 else None

    @computed_field(json_schema_extra={"attribute": True, "attribute_name": "ws-send"})  # type: ignore
    @property
    def ws_send(self) -> str | None:
        return "" if len(self.reactive_methods) > 0 else None

    @computed_field()  # type: ignore
    @property
    def reactive_methods(self) -> dict[str, Callable]:
        return dict(self.get_triggers_and_methods())

    def _add_classes(self, element: LxmlElement):
        container = []
        for source in [self.classes, self._base_classes]:
            _rendered = source.render()
            if _rendered:
                container.append(_rendered)
        if container:
            element.set("class", " ".join(container))

    def get_reactive_attributes(self):
        fields = []
        for field_name in self.model_fields.keys():
            attr = getattr(self, field_name)
            if attr is not None and isinstance(attr, ReactiveBase):
                fields.append(attr)
        return fields

    def get_triggers_and_methods(self):
        for attr in dir(self):
            if (
                attr not in ["__fields__", "__fields_set__", "__signature__"]
                and attr not in self.model_computed_fields.keys()
            ):
                if callable(getattr(self, attr)):
                    method = getattr(self, attr)
                    if hasattr(method, "trigger") and method.trigger:
                        yield method.trigger, method

    def get_methods_with_attribute(self, attribute: str):
        for attr in dir(self):
            if (
                attr not in ["__fields__", "__fields_set__", "__signature__"]
                and attr not in self.model_computed_fields.keys()
            ):
                if callable(getattr(self, attr)):
                    method = getattr(self, attr)
                    if hasattr(method, attribute):
                        yield method

    async def before_render(self):
        pass

    def inject_page_reference(self, page: Any):
        for element in self.traverse():
            if isinstance(element, Element):
                for attr_name, field in element.model_fields.items():
                    if field.json_schema_extra and field.json_schema_extra.get("page_reference"):
                        setattr(element, attr_name, page)


T = TypeVar("T", bound=Element)  # todo- add strict typing for Element


class Collection(ReactiveBase[list[T]]):
    def __init__(self, value: list[T] | None = None):
        super().__init__(value=value)

    def __repr__(self):
        return f"<Collection {self._value}>"

    def __str__(self):
        return f"<Collection {self._value}>"


class Reactive(ReactiveBase[T]):
    ...
