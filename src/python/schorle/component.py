from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

from schorle.controller import WithController
from schorle.element import Element
from schorle.prototypes import ElementPrototype
from schorle.tags import HTMLTag


class Component(ElementPrototype, WithController, ABC):
    tag: HTMLTag = HTMLTag.COMPONENT

    def model_post_init(self, __context: Any) -> None:
        self.element_id = f"cid-{str(uuid4())[0:8]}"
        if self.controller:
            self()

    def __call__(self):
        with Element(tag=self.tag, element_id=self.element_id):
            self.render()

    @abstractmethod
    def render(self):
        pass
