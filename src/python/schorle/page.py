from __future__ import annotations

import contextvars
from abc import ABC
from asyncio import Queue

from pydantic import Field, PrivateAttr

from schorle.controller import WithController
from schorle.element import div
from schorle.tags import HTMLTag
from schorle.types import Reactives
from schorle.with_attributes import WithAttributes


class Page(WithAttributes, WithController, ABC):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"
    _token: contextvars.Token | None = PrivateAttr()
    render_queue: Queue[WithAttributes] = Field(default_factory=Queue)
    reactives: Reactives = Field(default_factory=dict)

    def __enter__(self):
        self._token = PAGE.set(self)
        self.controller.inside_page = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        PAGE.reset(self._token)
        self.controller.inside_page = False
        self.reactives = self.controller.reactives
        pass

    def __call__(self):
        with div(**self._prepare_element_kwargs()):
            self.render()


PAGE: contextvars.ContextVar[Page | None] = contextvars.ContextVar("page", default=None)
