from __future__ import annotations

import contextvars
from abc import ABC
from asyncio import Queue
from typing import Any

from pydantic import Field, PrivateAttr
from starlette.websockets import WebSocket

from schorle.attrs import Suspense
from schorle.controller import WithController
from schorle.element import div
from schorle.state import ReactiveModel
from schorle.tags import HTMLTag
from schorle.types import Reactives
from schorle.with_attributes import WithAttributes


class Page(WithAttributes, WithController, ABC):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"
    _token: contextvars.Token | None = PrivateAttr()
    reactives: Reactives = Field(default_factory=dict)
    render_queue: Queue = Field(default_factory=Queue)
    io: WebSocket | None = None
    _suspend_generators: dict[ReactiveModel, Suspense] = PrivateAttr(default_factory=dict)

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
        self._suspend_generators.update({s.on: s for s in self.controller.suspenses})

        for on, suspense in self._suspend_generators.items():

            async def emit_suspense(_suspense=suspense):  # we need to capture the suspense in a closure
                await self.render_queue.put(_suspense.render)

            for effector in on.get_effectors():
                effector.method.clear_pre_actions()
                effector.method.prepend(emit_suspense)

    def __call__(self):
        with div(**self._prepare_element_kwargs()):
            self.render()

    def initialize(self):
        pass

    def bind(self, reactive_model: ReactiveModel):
        def _emitter():
            self.render_queue.put_nowait(self)

        for effector_info in reactive_model.get_effectors():
            effector_info.method.subscribe(_emitter)


PAGE: contextvars.ContextVar[Page | None] = contextvars.ContextVar("page", default=None)
