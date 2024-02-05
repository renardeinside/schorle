from pydantic import Field
from pydantic.fields import computed_field

from schorle.attribute import Attribute
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag
from schorle.reactives.base import ReactiveBase
from schorle.reactives.classes import Classes
from schorle.utils import reactive


class Input(Element):
    tag: HTMLTag = HTMLTag.INPUT
    value: ReactiveBase[str] = Field(default=ReactiveBase(""), description="Value of the input field")
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


class Slider(Input):
    _base_classes: Classes = Classes("range", "form-control")
    input_type: str = Attribute(default="range", alias="type")
    minimum: int = 0
    maximum: int = 100

    @computed_field(json_schema_extra={"attribute": True, "attribute_name": "min"})  # type: ignore
    @property
    def min_attr(self) -> str | None:
        return str(self.minimum)

    @computed_field(json_schema_extra={"attribute": True, "attribute_name": "max"})  # type: ignore
    @property
    def max_attr(self) -> str | None:
        return str(self.maximum)
