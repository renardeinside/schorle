from __future__ import annotations

from typing import Any

from lxml import etree
from pydantic import PrivateAttr

from schorle.attrs import Classes
from schorle.controller import WithController
from schorle.tags import HTMLTag
from schorle.types import LXMLElement
from schorle.with_attributes import WithAttributes


class Element(WithAttributes, WithController):
    _pre_previous: LXMLElement | None = PrivateAttr(default=None)
    _element: LXMLElement | None = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        if self.controller:
            self.render()

    def get_lxml_element_attrs(self) -> dict[str, str]:
        _attributes = self.attrs or {}
        if self.element_id:
            _attributes["id"] = self.element_id

        if self.classes:
            _attributes["class"] = self.classes.render()

        if self.style:
            _attributes["style"] = ";".join([f"{k}:{v}" for k, v in self.style.items()])

        return _attributes

    def __call__(self):
        self.render()
        return self

    def render(self):
        self._element = etree.SubElement(self.controller.current, self.tag, **self.get_lxml_element_attrs())

    def __enter__(self):
        self._pre_previous = self.controller.previous
        self.controller.previous = self.controller.current
        if self._element is not None:
            self.controller.current = self._element

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.controller.current = self.controller.previous
        self.controller.previous = self._pre_previous


def element_function_factory(tag: HTMLTag):
    def func(
        element_id: str | None = None,
        classes: Classes | None = None,
        style: dict[str, str] | None = None,
        attrs: dict[str, str] | None = None,
        **attributes,
    ):
        combined_attrs = {**attributes, **(attrs or {})}
        return Element(
            tag=tag,
            element_id=element_id,
            classes=classes,
            style=style,
            attrs=combined_attrs,
        )

    return func


div = element_function_factory(HTMLTag.DIV)
span = element_function_factory(HTMLTag.SPAN)
button = element_function_factory(HTMLTag.BUTTON)
input_ = element_function_factory(HTMLTag.INPUT)
a = element_function_factory(HTMLTag.A)
img = element_function_factory(HTMLTag.IMG)
script = element_function_factory(HTMLTag.SCRIPT)
link = element_function_factory(HTMLTag.LINK)
meta = element_function_factory(HTMLTag.META)
title = element_function_factory(HTMLTag.TITLE)
head = element_function_factory(HTMLTag.HEAD)
body = element_function_factory(HTMLTag.BODY)
html = element_function_factory(HTMLTag.HTML)
p = element_function_factory(HTMLTag.P)
h1 = element_function_factory(HTMLTag.H1)
h2 = element_function_factory(HTMLTag.H2)
h3 = element_function_factory(HTMLTag.H3)
h4 = element_function_factory(HTMLTag.H4)
h5 = element_function_factory(HTMLTag.H5)
h6 = element_function_factory(HTMLTag.H6)
ul = element_function_factory(HTMLTag.UL)
ol = element_function_factory(HTMLTag.OL)
li = element_function_factory(HTMLTag.LI)
table = element_function_factory(HTMLTag.TABLE)
tr = element_function_factory(HTMLTag.TR)
td = element_function_factory(HTMLTag.TD)
th = element_function_factory(HTMLTag.TH)
form = element_function_factory(HTMLTag.FORM)
footer = element_function_factory(HTMLTag.FOOTER)
icon = element_function_factory(HTMLTag.ICON)
