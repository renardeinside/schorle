from schorle.elements.base import BaseElement, InputElement, OnClickElement
from schorle.reactive import Reactive


def div(*children, cls=None, **attrs):
    element = BaseElement("div", cls=cls, **attrs)
    for c in children:
        if isinstance(c, BaseElement):
            msg = """
            Elements shall be added to the div using the context manager, e.g.:
            with div():
                p("some text")
            """
            raise ValueError(msg)
    element.add(*children)
    return element


def head(*children, **attrs):
    element = BaseElement("head", **attrs)
    element.add(*children)
    return element


def html(*children, **attrs):
    element = BaseElement("html", **attrs)
    element.add(*children)
    return element


def link(**attrs):
    return BaseElement("link", **attrs)


def meta(**attrs):
    return BaseElement("meta", **attrs)


def script(**attrs):
    element = BaseElement("script", **attrs)
    element.add("")  # adding empty string to make it a proper tag
    return element


def span(cls=None, **attrs):
    element = BaseElement("span", cls=cls, **attrs)
    element.add("")
    return element


def title(*children, **attrs):
    element = BaseElement("title", **attrs)
    element.add(*children)
    return element


def body(*children, **attrs):
    element = BaseElement("body", **attrs)
    element.add(*children)
    return element


def p(*children, **attrs):
    element = BaseElement("p", **attrs)
    element.add(*children)
    return element


def button(*children, on_click, cls=None, **attrs):
    element = OnClickElement("button", on_click=on_click, cls=cls, **attrs)
    element.add(*children)
    return element


def text_input(*children, bind: Reactive, cls=None, **attrs):
    cls = cls + " input w-full max-w-xs" if cls else "input w-full max-w-xs"
    attrs.update({"placeholder": "Type here"})
    attrs.update({"type": "text"})
    attrs.update({"class": cls})
    element = InputElement(bind, **attrs)
    element.add(*children)
    return element
