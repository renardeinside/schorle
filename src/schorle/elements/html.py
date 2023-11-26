from schorle.elements.base import BaseElement, OnChangeElement, OnClickElement


def div(*children, **attrs):
    return BaseElement("div", children=children, **attrs)


def input_(input_type: str, on_change, **attrs):
    attrs["type"] = input_type
    return OnChangeElement("input", children=None, on_change=on_change, **attrs)


def head(*children, **attrs):
    return BaseElement("head", children=children, **attrs)


def html(*children, **attrs):
    return BaseElement("html", children=children, **attrs)


def link(**attrs):
    return BaseElement("link", children=None, **attrs)


def meta(**attrs):
    return BaseElement("meta", children=None, **attrs)


def script(**attrs):
    return BaseElement("script", children=[""], **attrs)


def title(*children, **attrs):
    return BaseElement("title", children=children, **attrs)


def body(*children, **attrs):
    return BaseElement("body", children=children, **attrs)


def p(*children, depends_on=None, **attrs):
    return BaseElement("p", children=children, depends_on=depends_on, **attrs)


def button(*children, on_click, **attrs):
    return OnClickElement("button", children=children, on_click=on_click, **attrs)


def code(*children, **attrs):
    return BaseElement("code", children=children, **attrs)
