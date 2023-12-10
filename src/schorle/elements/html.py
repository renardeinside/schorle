from schorle.elements.base import Element
from schorle.elements.tags import HTMLTag


def div(*children, cls=None, **attrs):
    element = Element(HTMLTag.DIV, cls=cls, **attrs)
    if children:
        element.children.extend(children)
    return element


def head(*children, **attrs):
    element = Element(HTMLTag.HEAD, **attrs)
    if children:
        element.children.extend(children)
    return element


def html(*children, **attrs):
    element = Element(HTMLTag.HTML, **attrs)
    if children:
        element.children.extend(children)
    return element


def link(**attrs):
    return Element(HTMLTag.LINK, **attrs)


def meta(**attrs):
    return Element(HTMLTag.META, **attrs)


def script(**attrs):
    element = Element(HTMLTag.SCRIPT, **attrs)
    element.children.append("")  # adding empty string to make it a proper tag
    return element


def span(cls=None, **attrs):
    element = Element(HTMLTag.SPAN, cls=cls, **attrs)
    element.children.append("")
    return element


def title(*children, **attrs):
    element = Element(HTMLTag.TITLE, **attrs)
    if children:
        element.children.extend(children)
    return element


def body(*children, **attrs):
    element = Element(HTMLTag.BODY, **attrs)
    if children:
        element.children.extend(children)
    return element


def p(*children, **attrs):
    element = Element(HTMLTag.P, **attrs)
    if children:
        element.children.extend(children)
    return element


def button(*children, **attrs):
    element = Element(HTMLTag.BUTTON, **attrs)
    if children:
        element.children.extend(children)
    return element
