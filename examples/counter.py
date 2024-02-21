from __future__ import annotations

from pydantic import Field

from schorle.app import Schorle
from schorle.button import Button
from schorle.classes import Classes
from schorle.component import Component
from schorle.effector import effector
from schorle.element import div
from schorle.on import On
from schorle.page import Page
from schorle.state import ReactiveModel
from schorle.text import text
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


class Counter(ReactiveModel):
    count: int = 0

    @effector
    async def increment(self):
        self.count += 1

    @effector
    async def decrement(self):
        self.count -= 1


class StatefulButton(Component):
    counter: Counter

    def render(self):
        with Button(on=On("click", self.counter.increment), modifier="primary"):
            text("Click me" if self.counter.count == 0 else f"Clicked {self.counter.count} times")

    def initialize(self):
        self.bind(self.counter)


class PageWithButton(Page):
    counter: Counter = Field(default_factory=Counter)

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            StatefulButton(counter=self.counter)


@app.get("/")
def get_page():
    return PageWithButton()
