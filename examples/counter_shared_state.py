from __future__ import annotations

from pydantic import Field

from schorle.app import Schorle
from schorle.classes import Classes
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


class PageWithButton(Page):
    counter: Counter = Field(default_factory=Counter)

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            with div(classes=Classes("flex flex-row justify-center items-center space-x-4")):
                with button(on=On("click", self.counter.increment), classes=Classes("btn btn-primary")):
                    text("Increment")
                with button(on=On("click", self.counter.decrement), classes=Classes("btn btn-secondary")):
                    text("Decrement")
            with div(classes=Classes("text-2xl")):
                text(f"Counter: {self.counter.value}")

    def __init__(self):
        super().__init__()
        self.bind(self.counter)


@app.get("/")
def get_page():
    return PageWithButton()
