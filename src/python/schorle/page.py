from __future__ import annotations

import contextvars
from abc import ABC
from typing import Any

from pydantic import Field, PrivateAttr

from schorle.bindable import Bindable
from schorle.controller import WithController
from schorle.element import div
from schorle.tags import HTMLTag
from schorle.types import Reactives
from schorle.with_attributes import WithAttributes


class Page(WithAttributes, WithController, Bindable, ABC):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"
    _token: contextvars.Token | None = PrivateAttr()
    reactives: Reactives = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        self.initialize()

    def __enter__(self):
        self._token = PAGE.set(self)
        self.controller.inside_page = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        PAGE.reset(self._token)
        self.controller.inside_page = False
        self.reactives.update(self.controller.reactives)
        pass

    def __call__(self):
        with div(**self._prepare_element_kwargs()):
            self.render()

    def initialize(self):
        pass


PAGE: contextvars.ContextVar[Page | None] = contextvars.ContextVar("page", default=None)
