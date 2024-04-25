from __future__ import annotations

from schorle.prototypes import ElementPrototype
from schorle.rendering_context import RENDERING_CONTEXT
from schorle.tags import HTMLTag


class Element(ElementPrototype):

    def __init__(self, **data):
        super().__init__(**data)
        if not RENDERING_CONTEXT.get():
            raise RuntimeError("Element must be created inside a rendering context")
        else:
            RENDERING_CONTEXT.get().append(self)

    def __enter__(self):
        RENDERING_CONTEXT.get().become_parent(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        RENDERING_CONTEXT.get().reset_parent()

    def __repr__(self):
        return f"<{self.tag}>"

    def __str__(self):
        return self.__repr__()


def element_function_factory(tag: HTMLTag):
    def func(style: dict[str, str] | None = None, element_id: str | None = None, **kwargs):
        return Element(
            tag=tag,
            element_id=element_id,
            style=style,
            on=kwargs.pop("on", None),
            bind=kwargs.pop("bind", None),
            attrs=kwargs,
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
main = element_function_factory(HTMLTag.MAIN)
