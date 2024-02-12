from __future__ import annotations

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
    count: int = 0

    @effector
    async def increment(self):
        self.count += 1

    @effector
    async def decrement(self):
        self.count -= 1


class Button(Component):
    counter: Counter

    def render(self):
        with button(on=On("click", self.counter.increment), classes=Classes("btn btn-primary")):
            text(f"Clicked {self.counter.count} times")

    def __init__(self, **data):
        super().__init__(**data)
        self.bind(self.counter)

    def bind(self, reactive: ReactiveModel):
        for _effector in reactive.get_effectors():
            print(_effector)
            # _effector.subscribe(self.render)


class PageWithButton(Page):
    def render(self):
        with div(classes=Classes("flex justify-center items-center h-screen")):
            Button(counter=Counter()).add()


@app.get("/")
def get_page():
    return PageWithButton()
