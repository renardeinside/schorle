from __future__ import annotations

from typing import Any

import msgpack
from pydantic import Field

from schorle.classes import Classes
from schorle.component import Component
from schorle.ref import Ref
from schorle.tags import HTMLTag


class TextInput(Component):
    tag: HTMLTag = HTMLTag.INPUT
    base_classes: Classes = Field(default_factory=lambda: Classes("input", "form-control"))
    placeholder: str = ""
    value: str = ""

    def model_post_init(self, __context: Any):
        self.classes.append(self.base_classes)
        self.attributes["placeholder"] = self.placeholder
        self.attributes["value"] = self.value
        super().model_post_init(__context)

    def render(self):
        pass


class FileInput(Component):
    tag: HTMLTag = HTMLTag.INPUT
    base_classes: Classes = Field(default_factory=lambda: Classes("file-input", "form-control"))
    multiple: bool = False
    ref: Ref | None = None

    def model_post_init(self, __context: Any):
        self.classes.append(self.base_classes)
        self.attributes["type"] = "file"
        if self.ref:
            self.ref.set(self)
        if self.multiple:
            self.attributes["multiple"] = "true"
        self.attributes["value"] = ""
        super().model_post_init(__context)

    async def clear(self):
        msg = msgpack.packb({"action": "clear", "target": self.element_id})
        await self._page_ref._io.send_bytes(msg)

    def render(self):
        pass
