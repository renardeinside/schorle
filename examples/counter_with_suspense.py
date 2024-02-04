from __future__ import annotations

import asyncio
from random import random

from schorle.app import Schorle
from schorle.effector import effector
from schorle.elements.button import Button
from schorle.elements.page import Page
from schorle.reactives.classes import Classes
from schorle.reactives.state import ReactiveModel
from schorle.utils import reactive

app = Schorle()


class Counter(ReactiveModel):
    value: int = 0

    @effector
    async def increment(self):
        self.value += 1


class ButtonWithCounter(Button):
    counter: Counter = Counter.factory()

    @reactive("click")
    async def handle(self):
        async with self.suspend():
            # Simulate a slow network request
            await asyncio.sleep(random() * 3)  # noqa: S311
            await self.counter.increment()

    async def _on_increment(self, counter: Counter):
        await self.text.update(f"Clicked {counter.value} times")
        await self.classes.toggle("btn-success")

    async def before_render(self):
        await self.counter.increment.subscribe(self._on_increment)


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen space-y-4")
    first_button: ButtonWithCounter = ButtonWithCounter.factory()
    second_button: ButtonWithCounter = ButtonWithCounter.factory()


@app.get("/")
def get_page():
    return PageWithButton()
