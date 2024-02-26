from __future__ import annotations

import asyncio

from schorle.app import Schorle
from schorle.attrs import Classes, On, Suspense
from schorle.button import Button
from schorle.component import Component
from schorle.element import div
from schorle.loading import Loading
from schorle.page import Page
from schorle.state import ReactiveModel, effector
from schorle.text import text

app = Schorle()


class Counter(ReactiveModel):
    count: int = 0

    @effector
    async def increment(self, _):
        await asyncio.sleep(1)
        self.count += 1


class StatefulButton(Component):
    counter: Counter = Counter.factory()
    modifier: str | None = None

    def render(self):
        with Button(
            on=On("click", self.counter.increment),
            classes=Classes("w-48"),
            modifier=self.modifier,
            suspense=Suspense(on=self.counter, fallback=Loading()),
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
