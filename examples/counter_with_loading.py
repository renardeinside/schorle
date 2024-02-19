from __future__ import annotations

import asyncio

from schorle.app import Schorle
from schorle.button import Button
from schorle.classes import Classes
from schorle.component import Component
from schorle.effector import effector
from schorle.element import div
from schorle.loading import Loading
from schorle.on import On
from schorle.page import Page
from schorle.state import ReactiveModel
from schorle.suspense import Suspense
from schorle.text import text

app = Schorle()


class Counter(ReactiveModel):
    count: int = 0

    @effector
    async def increment(self):
        await asyncio.sleep(1)
        self.count += 1


class StatefulButton(Component):
    counter: Counter = Counter.factory()
    modifier: str | None = None

    def render(self):
        with Button(
            on=On("click", self.counter.increment),
            suspense=Suspense(on=self.counter, fallback=Loading()),
            classes=self.classes.append("w-48"),
            modifier=self.modifier,
        ):
            text("Click me" if self.counter.count == 0 else f"Clicked {self.counter.count} times")

    def initialize(self):
        self.bind(self.counter)


class PageWithButton(Page):

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            with div(classes=Classes("space-y-2")):
                StatefulButton(modifier="primary")
                StatefulButton(modifier="secondary")


@app.get("/")
def get_page():
    return PageWithButton()
