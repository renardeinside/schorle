from asyncio import iscoroutinefunction
from contextlib import contextmanager
from typing import Awaitable, Callable, Optional

from pydantic import Field

from schorle.elements.attribute import Attribute
from schorle.elements.base import Element, ElementWithGeneratedId
from schorle.elements.tags import HTMLTag

OnClick = Callable[..., Awaitable]


class Button(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.BUTTON
    on_click: Optional[OnClick] = Field(default=None, description="Handler for on_click event")
    disabled: bool = Field(default=False)
    classes: str = Field(default="btn")
    send: str = Attribute(default="", alias="ws-send", private=True)
    hx_swap: str = Attribute(default="morph", alias="hx-swap-oob")

    def __init__(self, **data):
        super().__init__(**data)
        if "disabled" in data and data["disabled"]:
            self.disable()

    def set_callback(self, callback: Callable):
        """
        Set the callback for the on_click event.
        If the callback is not a coroutine, it will be wrapped in one.
        """
        if not iscoroutinefunction(callback):

            async def _callback():
                callback()

        else:
            _callback = callback
        self.on_click = _callback

    def disable(self):
        self.disabled = True
        if "btn-disabled" not in self.classes:
            self.classes += " btn-disabled"

    def enable(self):
        self.disabled = False
        self.classes = self.classes.replace(" btn-disabled", "")

    @contextmanager
    def suspend(self, suspense: Optional[Element] = None):
        _callback = self.on_click
        self.set_callback(lambda: None)
        with super().suspend(suspense):
            yield self
        self.set_callback(_callback)
