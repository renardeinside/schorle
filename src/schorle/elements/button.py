from typing import Awaitable, Callable

from pydantic import Field

from schorle.elements.base.element import Element
from schorle.elements.base.mixins import SendMixin
from schorle.elements.tags import HTMLTag
from schorle.observables.classes import Classes

OnClick = Callable[..., Awaitable]


class Button(Element):
    tag: HTMLTag = HTMLTag.BUTTON
    _base_classes: Classes = Classes("btn")
    classes: Classes = Classes()


class ReactiveButton(Button, SendMixin):
    _base_classes: Classes = Classes("btn")
    classes: Classes = Classes()
    callback: OnClick | None = Field(default=None, description="Callback to be executed on click")

    def __init__(self, **data):
        super().__init__(**data)
        if self.callback is not None and type(self).on_click != ReactiveButton.on_click:
            msg = "Cannot set callback and override on_click at the same time"
            raise msg
        elif self.on_click != ReactiveButton.on_click:
            self.callback = self.on_click

    async def on_click(self):
        pass

    def __setattr__(self, key, value):
        if key == "on_click":
            self.callback = value
        super().__setattr__(key, value)
