from collections.abc import Awaitable, Callable

from pydantic import PrivateAttr

from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag
from schorle.reactives.classes import Classes

OnClick = Callable[..., Awaitable]


class Button(Element):
    tag: HTMLTag = HTMLTag.BUTTON
    _base_classes: Classes = Classes("btn")
    _additional_callbacks: list = PrivateAttr(default_factory=list)
    classes: Classes = Classes()

    def add_callback(self, trigger: str, callback: Callable):
        self._additional_callbacks.append((trigger, callback))

    def get_triggers_and_methods(self):
        for trigger, method in super().get_triggers_and_methods():
            yield trigger, method
        for trigger, callback in self._additional_callbacks:
            yield trigger, callback
