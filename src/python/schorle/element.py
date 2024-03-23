from __future__ import annotations

from functools import partial
from http import HTTPStatus
from typing import Any, Callable

from lxml import etree
from starlette.responses import HTMLResponse

from schorle.attrs import Classes, Reactive
from schorle.prototypes import ElementPrototype
from schorle.tags import HTMLTag
from schorle.types import LXMLElement
from schorle.utils import fix_self_closing_tags


class Element(ElementPrototype):
    post_callback: Callable[[Element], Any] | None = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.post_callback:
            self.post_callback(self)

    def render(self, *, pretty_print: bool = True) -> str:
        _composed = self._compose(self)
        return etree.tostring(_composed, pretty_print=pretty_print, encoding="utf-8").decode("utf-8")

    def to_response(self, status_code: HTTPStatus = HTTPStatus.OK, *args, **kwargs) -> HTMLResponse:
        return HTMLResponse(self.render(), status_code.value, *args, **kwargs)

    def _compose(self, element: ElementPrototype) -> LXMLElement:
        _element = element.to_lxml()
        for child in element.get_children():
            _element.append(self._compose(child))
        fix_self_closing_tags(_element)
        return _element

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getattr__(self, name):
        if name.upper() in HTMLTag.__members__:

            def post_callback(element: Element):
                self.append(element)

            _factory = element_function_factory(HTMLTag[name.upper()])
            return partial(_factory, post_callback=post_callback)
        return super().__getattr__(name)

    def __rshift__(self, other):
        self.append(other)
        return self


def element_function_factory(tag: HTMLTag):
    def func(
        classes: Classes | None = None,
        element_id: str | None = None,
        style: dict[str, str] | None = None,
        attrs: dict[str, str] | None = None,
        reactive: Reactive | None = None,
        hsx: str | None = None,
        post_callback: Callable[[Element], Any] | None = None,
        **attributes,
    ):
        combined_attrs = {**attributes, **(attrs or {})}
        if hsx:
            combined_attrs["data-script"] = str(hsx)
        return Element(
            tag=tag,
            element_id=element_id,
            classes=classes,
            style=style,
            reactive=reactive,
            attrs=combined_attrs,
            post_callback=post_callback,
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
