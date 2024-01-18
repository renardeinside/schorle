from types import MethodType
from typing import Awaitable, Callable

from pydantic import PrivateAttr

from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag
from schorle.dynamics.classes import Classes

OnClick = Callable[..., Awaitable]


class Button(Element):
    tag: HTMLTag = HTMLTag.BUTTON
    _base_classes: Classes = Classes("btn")
    _additional_callbacks: list = PrivateAttr(default_factory=list)
    classes: Classes = Classes()

    def add_callback(self, trigger: str, callback: MethodType | OnClick):
        self._additional_callbacks.append((trigger, callback))

    def get_triggers_and_methods(self):
        for trigger, method in super().get_triggers_and_methods():
            yield trigger, method
        for trigger, method in self._additional_callbacks:
            yield trigger, getattr(method.__self__, method.__name__)
