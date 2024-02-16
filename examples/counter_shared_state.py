from __future__ import annotations

from schorle.app import Schorle
from schorle.button import Button
from schorle.classes import Classes
from schorle.effector import effector
from schorle.element import div, p
from schorle.on import On
from schorle.page import Page
from schorle.state import ReactiveModel
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
    counter: Counter = Counter.factory()

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            with div(classes=Classes("flex flex-row justify-center items-center space-x-4")):
                with Button(on=On("click", self.counter.increment), modifier="primary"):
                    text("Increment")
                with Button(
                    on=On("click", self.counter.decrement),
                    modifier="secondary",
                    disabled=self.counter.value <= 0,
                ):
                    text("Decrement")
            with p(classes=Classes("text-2xl")):
                text(f"Counter: {self.counter.value}")

    def initialize(self):
        self.bind(self.counter)


@app.get("/")
def get_page():
    return PageWithButton()
