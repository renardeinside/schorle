from typing import Any

from pydantic import Field

from schorle.classes import Classes
from schorle.component import Component
from schorle.tags import HTMLTag


class TextInput(Component):
    tag: HTMLTag = HTMLTag.INPUT
    base_classes: Classes = Field(default_factory=lambda: Classes("input", "form-control"))
    placeholder: str = ""
    value: str = ""
    name: str = Field(default="default")

    def model_post_init(self, __context: Any):
        self.classes.append(self.base_classes)
        self.attributes["placeholder"] = self.placeholder
        self.attributes["value"] = self.value
        self.attributes["hx-include"] = "this"
        self.attributes["name"] = self.name
        super().model_post_init(__context)

    def render(self):
        pass
