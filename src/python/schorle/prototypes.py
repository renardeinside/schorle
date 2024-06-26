from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from schorle.attrs import Bind, On, _When
from schorle.session import Session
from schorle.tags import HTMLTag


class ElementPrototype(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tag: HTMLTag | str
    element_id: str | None = None
    _children: list[ElementPrototype] = PrivateAttr(default_factory=list)
    _parent: ElementPrototype | None = PrivateAttr(default=None)
    _text: str | None = PrivateAttr(default=None)
    attrs: dict[str, str] = Field(default_factory=dict)
    classes: _When | str | list[str] | list[str | _When] | None = None
    style: dict[str, str] | None = None
    on: On | list[On] | None = None
    bind: Bind | None = None
    session: Session | None = None

    def append(self, element: ElementPrototype):
        element._parent = self
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
        self._parent = None
        self._text = None

    def set_parent(self, parent: ElementPrototype):
        self._parent = parent

    def get_parent(self) -> ElementPrototype | None:
        return self._parent
