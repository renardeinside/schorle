from pydantic import Field

from schorle.elements.attribute import Attribute
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag
from schorle.dynamics.base import Dynamic
from schorle.dynamics.classes import Classes
from schorle.utils import reactive


class Input(Element):
    tag: HTMLTag = HTMLTag.INPUT
    value: Dynamic[str] = Field(default=Dynamic(""), description="Value of the input field")
    _base_classes: Classes = Classes("input", "form-control")
    hx_include: str = Attribute(default="this", alias="hx-include", private=True)
    placeholder: str | None = Attribute(default=None)
    name: str = Attribute(default="default")
    input_type: str = Attribute(default="text", alias="type")

    def __init__(self, **data):
        super().__init__(**data)
        self.name = self.element_id

    async def clear(self):
        await self.value.update("")

    @reactive("change")
    async def on_change(self, new_value: str):
        await self.value.update(new_value, skip_render=True)
