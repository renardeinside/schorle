import pkgutil

from lxml import etree
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import PrivateAttr

from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag


class Icon(Element):
    tag: HTMLTag = HTMLTag.SVG
    width: str | int = 24
    height: str | int = 24
    name: str
    _payload: str = PrivateAttr(default="")

    def __init__(self, **data):
        super().__init__(**data)
        self._payload = pkgutil.get_data("schorle", f"assets/feather/{self.name}.svg").decode("utf-8")

    def get_prerender(self) -> LxmlElement:
        elem = etree.fromstring(self._payload)  # noqa: S320 since we trust the source
        elem.attrib["width"] = str(self.width)
        elem.attrib["height"] = str(self.height)
        return elem

    def __repr__(self):
        return tostring(self.get_prerender(), pretty_print=False).decode("utf-8")
