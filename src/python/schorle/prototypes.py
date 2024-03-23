from __future__ import annotations

from lxml import etree
from pydantic import BaseModel, PrivateAttr

from schorle.attrs import Classes, Reactive
from schorle.tags import HTMLTag
from schorle.types import LXMLElement


class ElementPrototype(BaseModel):
    tag: HTMLTag
    element_id: str | None = None
    classes: Classes | None = None
    style: dict[str, str] | None = None
    attrs: dict[str, str] | None = None
    reactive: Reactive | None = None
    _children: list[ElementPrototype] = PrivateAttr(default_factory=list)
    _text: str | None = PrivateAttr(default=None)

    def append(self, *children: ElementPrototype):
        for child in children:
            self._children.append(child)
        return self

    def get_children(self) -> list[ElementPrototype]:
        return self._children

    def to_lxml(self) -> LXMLElement:
        _element = etree.Element(self.tag.value)
        for k, v in self.get_lxml_element_attrs().items():
            _element.set(k, v)

        if self._text:
            _element.text = self._text
        return _element

    def get_lxml_element_attrs(self) -> dict[str, str]:
        _attributes = self.attrs or {}
        if self.element_id:
            _attributes["id"] = self.element_id

        if self.classes:
            _attributes["class"] = self.classes.render()

        if self.style:
            _attributes["style"] = ";".join([f"{k}:{v}" for k, v in self.style.items()])

        if self.reactive:
            _attributes.update(self.reactive.render())

        return _attributes

    def text(self, text: str):
        self._text = text
        return self
