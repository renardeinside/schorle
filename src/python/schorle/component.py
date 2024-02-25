from abc import ABC
from typing import Any
from uuid import uuid4

from schorle.bindable import Bindable
from schorle.controller import WithController
from schorle.element import Element
from schorle.page import PAGE, Page
from schorle.tags import HTMLTag
from schorle.with_attributes import WithAttributes


class Component(WithAttributes, WithController, Bindable, ABC):
    tag: HTMLTag = HTMLTag.DIV
    page_ref: Page | None = None
    instant_render: bool = True

    def model_post_init(self, __context: Any) -> None:
        self.page_ref = PAGE.get()

        if not self.element_id and self.page_ref:
            self.element_id = f"sle-{self.tag}-{str(uuid4())[:8]}"

        self.initialize()
        if self.controller and self.instant_render:
            self()

    def __call__(self):

        with Element(tag=self.tag, **self._prepare_element_kwargs()):
            self.render()

    def initialize(self):
        pass
