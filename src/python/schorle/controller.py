from __future__ import annotations

import contextvars
from typing import Any, Callable

from lxml import etree

from schorle.attrs import Suspense
from schorle.types import LXMLElement, Reactives


def fix_self_closing_tags(element: LXMLElement) -> None:
    for elem in element.iter():
        if len(elem) == 0 and elem.text is None:
            elem.text = ""


class RenderController:

    def __init__(self):
        self._root: LXMLElement = etree.Element("root")
        self.previous: LXMLElement = self._root
        self.current: LXMLElement = self._root
        self.component_root: LXMLElement | None = None
        self.inside_page: bool = False
        self._token: Any | None = None
        self.reactives: Reactives = {}
        self.suspenses: list[Suspense] = []

    def get_root(self) -> LXMLElement:
        return self._root

    def __enter__(self):
        self._token = RENDER_CONTROLLER.set(self)
        self.suspenses = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        RENDER_CONTROLLER.reset(self._token)

    def render(self, renderable: Callable) -> LXMLElement:
        renderable()
        fix_self_closing_tags(self.get_root())
        return self.get_root().getchildren()[0]


RENDER_CONTROLLER: contextvars.ContextVar[RenderController | None] = contextvars.ContextVar(
    "render_controller", default=None
)


class WithController:

    @property
    def controller(self) -> RenderController | None:
        return RENDER_CONTROLLER.get()
