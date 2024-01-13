from typing import Awaitable, Callable

from pydantic import Field

from schorle.elements.base.element import Element
from schorle.elements.base.mixins import SendMixin
from schorle.elements.classes import Classes
from schorle.elements.tags import HTMLTag

OnClick = Callable[..., Awaitable]


class Button(Element, SendMixin):
    tag: HTMLTag = HTMLTag.BUTTON
    disabled: bool = Field(default=False)
    _base_classes: Classes = Classes("btn")

    async def on_click(self):
        pass
