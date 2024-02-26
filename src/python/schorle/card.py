from typing import Callable

from schorle.attrs import Classes
from schorle.component import Component
from schorle.element import div, h2
from schorle.text import text


class Card(Component):
    base_classes: Classes = Classes("card bg-base-200")
    title: str | None = None
    body: Component | Callable | None = None

    def initialize(self):
        self.classes = self.classes.append(self.base_classes) if self.classes else self.base_classes

    def render(self):
        with div(classes=Classes("card-body")):
            with h2(classes=Classes("card-title")):
                if self.title:
                    text(self.title)
            if self.body:
                self.body()
