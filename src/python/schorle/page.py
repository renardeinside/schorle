from __future__ import annotations

from pydantic import PrivateAttr

from schorle.controller import WithController
from schorle.element import Element
from schorle.prototypes import ElementPrototype
from schorle.tags import HTMLTag


class Page(ElementPrototype, WithController):
    tag: HTMLTag = HTMLTag.PAGE
    _pre_previous: ElementPrototype | None = PrivateAttr(default=None)

    def render(self):
        self.controller.current.append(self)

    def __call__(self):
        with Element(tag=self.tag, attrs=self.attrs):
            self.render()
