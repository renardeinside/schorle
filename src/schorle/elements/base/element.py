from __future__ import annotations

from asyncio import Queue
from typing import AsyncIterator

from lxml.etree import _Element as LxmlElement
from pydantic import PrivateAttr

from schorle.elements.base.base import BaseElement
from schorle.elements.classes import Classes


class Element(BaseElement):
    _base_classes: Classes = PrivateAttr(default_factory=Classes)
    classes: Classes = Classes()
    _render_queue: Queue = PrivateAttr(default_factory=Queue)

    def __init__(self, **data):
        super().__init__(**data)
        if self.element_id is None:
            self.element_id = (
                f"schorle-{self.tag.value.lower()}-{id(self)}" if self.element_id is None else self.element_id
            )

    def _add_classes(self, element: LxmlElement):
        container = []
        for source in [self.classes, self._base_classes]:
            _rendered = source.render()
            if _rendered:
                container.append(_rendered)
        if container:
            element.set("class", " ".join(container))

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key in ["classes", "text", "style"]:
            self._render_queue.put_nowait(self)

    async def updates_emitter(self) -> AsyncIterator[Element]:
        while True:
            element = await self._render_queue.get()
            yield element
