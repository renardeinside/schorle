from schorle.elements.attribute import Attribute
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag


class Img(Element):
    tag: HTMLTag = HTMLTag.IMG
    src: str = Attribute(..., alias="src")
    alt: str = Attribute(..., alias="alt")
