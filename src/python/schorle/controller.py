from __future__ import annotations

import contextvars
from functools import partial
from typing import Any, Callable

from lxml import etree
from starlette.responses import HTMLResponse

from schorle.prototypes import ElementPrototype
from schorle.tags import HTMLTag
from schorle.types import LXMLElement


class RootElement(ElementPrototype):
    tag: HTMLTag = HTMLTag.ROOT


def fix_self_closing_tags(element: LXMLElement) -> None:
    for _tag in element.iter():
        if _tag.tag in ["script", "link", "i"]:
            if _tag.text is None:
                _tag.text = ""


class RenderController:

    def __init__(self):
        self.previous: ElementPrototype | None = None
        self.root: RootElement = RootElement()
        self.current: ElementPrototype = self.root
        self._token: Any | None = None

    def __enter__(self):
        self._token = RENDER_CONTROLLER.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        RENDER_CONTROLLER.reset(self._token)

    def render(self, renderable: Callable) -> LXMLElement:
        renderable()
        unwrapped = self.compose(self.root)[0]  # to unwrap the root element
        fix_self_closing_tags(unwrapped)
        return unwrapped

    def compose(self, element: ElementPrototype) -> LXMLElement:
        _element = element.to_lxml()
        for child in element.get_children():
            _element.append(self.compose(child))
        return _element


RENDER_CONTROLLER: contextvars.ContextVar[RenderController | None] = contextvars.ContextVar(
    "render_controller", default=None
)


class WithController:

    @property
    def controller(self) -> RenderController | None:
        return RENDER_CONTROLLER.get()


def render(renderable: Callable, *args, **kwargs) -> HTMLResponse:
    with RenderController() as rc:
        rendered = rc.render(partial(renderable, *args, **kwargs))
        _serialized = etree.tostring(rendered, pretty_print=True, doctype="<!DOCTYPE html>").decode("utf-8")
        return HTMLResponse(_serialized, status_code=200)
