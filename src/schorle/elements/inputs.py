from pydantic import Field

from schorle.elements.attribute import Attribute
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag
from schorle.observables.classes import Classes


class Input(Element):
    tag: HTMLTag = HTMLTag.INPUT
    _base_classes: Classes = Classes("input", "form-control")
    value: str = Field(default="")
    send: str = Attribute(default="", alias="ws-send", private=True)
    hx_include: str = Attribute(default="this", alias="hx-include", private=True)
    placeholder: str | None = Attribute(default=None)
    name: str = Attribute(default="default", private=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.name = self.element_id

    async def on_change(self, new_value: str):
        self.value = new_value

    async def clear(self):
        self.value = ""
        await self.update()