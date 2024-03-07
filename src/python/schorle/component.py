from abc import ABC
from typing import Any
from uuid import uuid4

from loguru import logger
from lxml import etree

from schorle.controller import RenderController, WithController
from schorle.element import Element
from schorle.models import Action, ServerMessage
from schorle.page import PAGE, Page
from schorle.state import ReactiveModel
from schorle.tags import HTMLTag
from schorle.with_attributes import WithAttributes


class Component(WithAttributes, WithController, ABC):
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

    def bind(self, reactive_model: ReactiveModel):

        for effector_info in reactive_model.get_effectors():
            logger.debug(f"Binding {effector_info.method} to {self}")
            effector_info.method.subscribe(self)

    async def emit(self):
        with RenderController() as rc:
            with self.page_ref:
                rendered = rc.render(self)
                _html = etree.tostring(rendered, pretty_print=True).decode()
                target = rendered.get("id")
            _msg = ServerMessage(target=target, payload=_html, action=Action.morph)
            # logger.debug(f"Sending message: {_msg}")
            await self.page_ref.io.send_bytes(_msg.encode())

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.element_id})/>"

    def __str__(self):
        return self.__repr__()
