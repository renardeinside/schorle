from __future__ import annotations

from pydantic import Field

from schorle.app import Schorle
from schorle.classes import Classes
from schorle.component import Component
from schorle.effector import effector
from schorle.element import button, div
from schorle.on import On
from schorle.page import Page
from schorle.reactives.state import ReactiveModel
from schorle.text import text

app = Schorle()


class Counter(ReactiveModel):
    value: int = 0

    @effector
    def increment(self):
        self.value += 1

    @effector
    def decrement(self):
        self.value -= 1


class View(Component):
    counter: Counter

    def render(self):
        with div(classes=Classes("text-2xl")):
            text(f"Counter: {self.counter.value}")

    def __init__(self, **data):
        super().__init__(**data)
        self.bind(self.counter)


class Buttons(Component):
    counter: Counter

    def render(self):
        with div(classes=Classes("flex flex-row justify-center items-center space-x-4")):
            with button(on=On("click", self.counter.increment), classes=Classes("btn btn-primary")):
                text("Increment")
            with button(
                on=On("click", self.counter.decrement),
                classes=Classes(f"btn btn-secondary {'btn-disabled' if self.counter.value <= 0 else ''}"),
            ):
                text("Decrement")

    def __init__(self, **data):
        super().__init__(**data)
        self.bind(self.counter)


class PageWithButton(Page):
    counter: Counter = Field(default_factory=Counter)

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-5/6")):
            Buttons(counter=self.counter)

        View(counter=self.counter)


@app.get("/")
def get_page():
    return PageWithButton()
