from lxml import etree

from schorle.classes import Classes
from schorle.context_vars import RenderControllerMixin
from schorle.on import On
from schorle.tags import HTMLTag


class Element(RenderControllerMixin):
    def __init__(
        self,
        tag: HTMLTag,
        element_id: str | None = None,
        classes: Classes | None = None,
        style: dict[str, str] | None = None,
        on: list[On] | On | None = None,
        **attributes,
    ):
        self.tag = tag.value
        self._element_id = element_id
        self._element = self.get_element()

        if attributes:
            for k, v in attributes.items():
                self._element.set(k, v)

        if style:
            self._element.set("style", ";".join([f"{k}: {v}" for k, v in style.items()]))
        if classes:
            _rendered = classes.render()
            if _rendered:
                self._element.set("class", _rendered)
        if element_id:
            self._element.set("id", self._element_id)
        if on:
            on = [on] if isinstance(on, On) else on
            self._element.set("ws-send", "")
            _triggers = ",".join([o.trigger for o in on])
            self._element.set("hx-trigger", _triggers)

    def get_element(self):
        elem = etree.SubElement(self.controller.current, self.tag)
        if self.tag in [HTMLTag.SCRIPT, HTMLTag.LINK]:
            elem.text = ""  # Prevents self-closing tags
        return elem

    def __enter__(self):
        self.controller.previous = self.controller.current
        self.controller.current = self._element

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.controller.current = self.controller.previous
        pass

    def add(self):
        with self:
            pass

    def __repr__(self):
        _id_str = f"id={self._element_id}" if self._element_id else ""
        return f"<{self.tag} {_id_str}/>"

    def __str__(self):
        return self.__repr__()


def element_function_factory(tag: HTMLTag):
    def func(
        element_id: str | None = None,
        classes: Classes | None = None,
        style: dict[str, str] | None = None,
        on: list[On] | On | None = None,
        **attributes,
    ):
        return Element(tag, element_id, classes, style, on, **attributes)

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
