from typing import Any

from pydantic import Field

from schorle.attrs import Classes
from schorle.component import Component
from schorle.models import Action, ServerMessage
from schorle.tags import HTMLTag


class TextInput(Component):
    tag: HTMLTag = HTMLTag.INPUT
    base_classes: Classes = Field(default_factory=lambda: Classes("input", "form-control"))
    placeholder: str = ""
    value: str = ""
    name: str = Field(default="default")

    def model_post_init(self, __context: Any):
        self.classes.append(self.base_classes)
        self.attrs["placeholder"] = self.placeholder
        self.attrs["value"] = self.value
        super().model_post_init(__context)

    def render(self):
        pass


class FileInput(Component):
    tag: HTMLTag = HTMLTag.INPUT
    base_classes: Classes = Field(default_factory=lambda: Classes("file-input", "form-control"))
    multiple: bool = False

    def model_post_init(self, __context: Any):
        self.classes.append(self.base_classes)
        self.attrs["type"] = "file"
        if self.multiple:
            self.attrs["multiple"] = "true"
        self.attrs["value"] = ""
        super().model_post_init(__context)

    async def clear(self):
        msg = ServerMessage(action=Action.clear, target=self.element_id)
        await self.page_ref.io.send_bytes(msg.encode())

    def render(self):
        pass
