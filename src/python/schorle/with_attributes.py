from __future__ import annotations

from abc import ABC

from pydantic import BaseModel, ConfigDict, Field

from schorle.attrs import Classes, On
from schorle.renderable import Renderable
from schorle.suspense import Suspense
from schorle.tags import HTMLTag


class WithAttributes(BaseModel, Renderable, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    tag: HTMLTag
    element_id: str | None = None
    classes: Classes | None = None
    style: dict[str, str] | None = None
    on: list[On] | On | None = None
    suspense: Suspense | None = None
    attrs: dict[str, str] | None = Field(default_factory=dict)

    def _prepare_element_kwargs(self):
        return {
            "element_id": self.element_id,
            "classes": self.classes,
            "style": self.style,
            "on": self.on,
            "suspense": self.suspense,
            "attrs": self.attrs,
        }
