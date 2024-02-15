from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from schorle.classes import Classes
from schorle.context_vars import RENDER_CONTROLLER, RenderControllerMixin
from schorle.element import Element
from schorle.reactives.state import ReactiveModel
from schorle.tags import HTMLTag


class Component(ABC, BaseModel, RenderControllerMixin):
    tag: HTMLTag = HTMLTag.DIV
    classes: Classes = Classes()
    style: dict[str, str] = Field(default_factory=dict)
    element_id: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)

    def add(self):
        pre_previous = self.controller.previous
        pre_current = self.controller.current

        with Element(self.tag, self.element_id, classes=self.classes, style=self.style, **self.attributes):
            self.render()

        self.controller.previous = pre_previous
        self.controller.current = pre_current

    def model_post_init(self, __context: Any) -> None:
        if RENDER_CONTROLLER.get().in_page_context:
            self.add()

    @abstractmethod
    def render(self):
        pass

    def __call__(self):
        self.add()

    def __repr__(self):
        return f"<{self.__class__.__name__}/>"

    def __str__(self):
        return self.__repr__()

    def bind(self, reactive: ReactiveModel):
        pass
