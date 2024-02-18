from __future__ import annotations

import asyncio

from pydantic import Field

from schorle.app import Schorle
from schorle.classes import Classes
from schorle.component import Component
from schorle.effector import effector
from schorle.element import button, div, span
from schorle.on import On
from schorle.page import Page
from schorle.state import ReactiveModel
from schorle.text import text

app = Schorle()


class Counter(ReactiveModel):
    count: int = 0

    @effector
    async def increment(self):
        await asyncio.sleep(1)
        self.count += 1


class Button(Component):
    counter: Counter

    def render(self):
        with button(on=On("click", self.counter.increment), classes=Classes("btn btn-primary")):
            with span(classes=Classes("htmx-indicator")):
                with span(classes=Classes("loading loading-infinity")):
                    text("")

            with div():
                text("Click me" if self.counter.count == 0 else f"Clicked {self.counter.count} times")

    def initialize(self):
        self.bind(self.counter)


class PageWithButton(Page):
    counter: Counter = Field(default_factory=Counter)

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            Button(counter=self.counter)


@app.get("/")
def get_page():
    return PageWithButton()
