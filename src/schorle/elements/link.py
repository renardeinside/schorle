from schorle.attribute import Attribute
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag


class Link(Element):
    tag: HTMLTag = HTMLTag.A
    href: str = Attribute(...)
