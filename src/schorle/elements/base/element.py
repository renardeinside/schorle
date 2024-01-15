from __future__ import annotations

from uuid import uuid4

from lxml.etree import _Element as LxmlElement
from pydantic import PrivateAttr

from schorle.elements.base.base import BaseElement
from schorle.observables.base import ObservableField
from schorle.observables.classes import Classes
from schorle.observables.trigger import Trigger


class Element(BaseElement):
    _base_classes: Classes = PrivateAttr(default_factory=Classes)
    _trigger: Trigger = PrivateAttr(default_factory=Trigger)
    classes: Classes = Classes()

    def __init__(self, **data):
        super().__init__(**data)
        if self.element_id is None:
            self.element_id = (
                f"schorle-{self.tag.value.lower()}-{id(self)}-{uuid4()!s}"
                if self.element_id is None
                else self.element_id
            )

    def _add_classes(self, element: LxmlElement):
        container = []
        for source in [self.classes, self._base_classes]:
            _rendered = source.render()
            if _rendered:
                container.append(_rendered)
        if container:
            element.set("class", " ".join(container))

    async def update(self):
        await self._trigger.update(str(uuid4()))

    def get_observable_fields(self):
        fields = [self._trigger]
        for field_name in self.model_fields.keys():
            attr = getattr(self, field_name)
            if attr is not None and isinstance(attr, ObservableField):
                fields.append(attr)
        return fields
