from typing import List

from pydantic import Field

from schorle.elements.attribute import Attribute
from schorle.elements.html import Div
from schorle.elements.inputs import Input
from schorle.observables.base import Observable
from schorle.observables.classes import Classes


class Tab(Div):
    render_behaviour: str = "flatten"
    input_field: Input = Field(default_factory=lambda: Input(input_type="radio", classes=Classes("tab"), role="tab"))
    content: Div = Field(default_factory=lambda: Div(classes=Classes("tab-content"), role="tabpanel"))


class TabsList(Div):
    role: str = Attribute("tablist")
    children: Observable[List[Tab]] = Field(default_factory=Observable)