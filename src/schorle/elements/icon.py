import requests
from lxml import etree
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import PrivateAttr

from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag


def get_icon_payload(name: str) -> str:
    url = f"https://raw.githubusercontent.com/feathericons/feather/main/icons/{name}.svg"
    return requests.get(url, timeout=10).text


class Icon(Element):
    tag: HTMLTag = HTMLTag.SVG
    width: str | int = 24
    height: str | int = 24
    name: str
    _payload: str = PrivateAttr(default="")

    def __init__(self, **data):
        super().__init__(**data)
        self._payload = get_icon_payload(self.name)

    def get_prerender(self) -> LxmlElement:
        # as per https://github.com/PyCQA/bandit/issues/767, this is not a security issue
        # we're using a secure parser and we're not using any user input
        parser = etree.XMLParser(ns_clean=True, resolve_entities=False, remove_blank_text=True)
        elem = etree.fromstring(self._payload, parser)  # noqa:S320
        elem.attrib["width"] = str(self.width)
        elem.attrib["height"] = str(self.height)
        return elem

    def __repr__(self):
        return tostring(self.get_prerender(), pretty_print=False).decode("utf-8")
