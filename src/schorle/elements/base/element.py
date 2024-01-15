from __future__ import annotations

from asyncio import Queue

from lxml.etree import _Element as LxmlElement
from pydantic import PrivateAttr

from schorle.elements.base.base import BaseElement
from schorle.observables.classes import Classes


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
