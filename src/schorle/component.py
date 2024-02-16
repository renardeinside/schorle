from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from schorle.classes import Classes
from schorle.element import Element
from schorle.on import On
from schorle.render_controller import RenderControllerMixin
from schorle.state import ReactiveModel
from schorle.tags import HTMLTag


class Component(ABC, BaseModel, RenderControllerMixin):
    tag: HTMLTag = HTMLTag.DIV
    classes: Classes = Field(default_factory=Classes)
    style: dict[str, str] = Field(default_factory=dict)
    element_id: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)
    on: list[On] | On = Field(default_factory=list)
    _page_ref: Any | None = None

    def add(self):
        pre_previous = self.controller.previous
        pre_current = self.controller.current
        self._page_ref = self.controller.page

        with Element(self.tag, self.element_id, classes=self.classes, style=self.style, on=self.on, **self.attributes):
            self.render()

        self.controller.previous = pre_previous
        self.controller.current = pre_current

    def model_post_init(self, __context: Any) -> None:
        if not self.element_id and self.tag not in [HTMLTag.HTML, HTMLTag.BODY]:
            self.element_id = f"sle-{self.tag}-{str(uuid4())[:8]}"

        self.initialize()

        if self.controller.page:
            self.add()

    def initialize(self):
        pass

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
        def _appender():
            self._page_ref.append_to_queue(self)

        for effector in reactive.get_effectors():
            effector.method.subscribe(_appender)
