from typing import Awaitable, Callable, Optional

from pydantic import Field

from schorle.elements.base.baseelement import Element
from schorle.elements.classes import Classes
from schorle.elements.tags import HTMLTag

OnClick = Callable[..., Awaitable]


class Button(Element):
    tag: HTMLTag = HTMLTag.BUTTON
    on_click: Optional[OnClick] = Field(default=None, description="Handler for on_click event")
    disabled: bool = Field(default=False)
    _base_classes: Classes = Classes("btn")
