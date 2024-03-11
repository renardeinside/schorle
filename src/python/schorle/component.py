from abc import ABC
from typing import Any
from uuid import uuid4

from schorle.controller import WithController
from schorle.element import Element
from schorle.page import PAGE, Page
from schorle.tags import HTMLTag
from schorle.with_attributes import WithAttributes


class Component(WithAttributes, WithController, ABC):
    tag: HTMLTag = HTMLTag.DIV
    page_ref: Page | None = None

    def model_post_init(self, __context: Any) -> None:
        self.page_ref = PAGE.get()

        if not self.element_id and self.page_ref:
            self.element_id = f"sle-{self.tag}-{str(uuid4())[:8]}"

        if self.controller:
            self()

    def __call__(self):

        with Element(tag=self.tag, **self._prepare_element_kwargs()):
            self.render()
