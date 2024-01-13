from pydantic import PrivateAttr

from schorle.elements.attribute import Attribute
from schorle.elements.base.element import Element
from schorle.elements.classes import Classes
from schorle.elements.tags import HTMLTag


class Input(Element):
    tag: HTMLTag = HTMLTag.INPUT
    _base_classes: Classes = Classes("input", "form-control")
    value: str | None = None
    send: str = Attribute(default="", alias="ws-send", private=True)
    hx_include: str = Attribute(default="this", alias="hx-include", private=True)
    placeholder: str | None = Attribute(default=None)
    name: str | None = Attribute(default=None, private=True)
    _trigger: str | None = PrivateAttr(default="")

    def __init__(self, **data):
        super().__init__(**data)
        self.name = self.element_id

    def clear(self):
        self._trigger = None
