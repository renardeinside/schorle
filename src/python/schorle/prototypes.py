from __future__ import annotations

from pydantic import BaseModel, Field, PrivateAttr

from schorle.tags import HTMLTag


class ElementPrototype(BaseModel):
    tag: HTMLTag | str
    element_id: str | None = None
    _children: list[ElementPrototype] = PrivateAttr(default_factory=list)
    _text: str | None = PrivateAttr(default=None)
    attrs: dict[str, str] = Field(default_factory=dict)
    classes: str | list[str] | None = None
    style: dict[str, str] | None = None

    def append(self, element: ElementPrototype):
        self._children.append(element)

    def set_text(self, text: str):
        self._text = text

    def get_children(self):
        return self._children

    def walk(self):
        for child in self._children:
            yield child
            yield from child.walk()

    def _cleanup(self):
        self._children = []
        self._text = None
