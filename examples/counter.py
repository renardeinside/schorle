from __future__ import annotations

from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.dynamics.classes import Classes
from schorle.dynamics.text import Text
from schorle.elements.button import Button
from schorle.elements.page import Page
from schorle.emitter import emitter, inject_emitters
from schorle.utils import before_render, reactive

app = Schorle()


class Counter(BaseModel, extra="allow"):
    value: int = 0

    @emitter
    async def increment(self):
        self.value += 1

    def __init__(self, **data):
        super().__init__(**data)


class ButtonWithCounter(Button):
    text: Text = Text("Click me!")
    counter: Counter

    @reactive("click")
    async def on_click(self):
        await self.counter.increment()

    @before_render
    async def prepare(self):
        inject_emitters(self.counter)

        async def _on_increment(counter: Counter):
            await self.text.update(f"Clicked {counter.value} times")

        self.counter.increment.subscribe(_on_increment)
        await _on_increment(self.counter)


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    first_button: ButtonWithCounter = Field(default_factory=lambda: ButtonWithCounter(counter=Counter()))
    second_button: ButtonWithCounter = Field(default_factory=lambda: ButtonWithCounter(counter=Counter()))


@app.get("/")
def get_page():
    return PageWithButton()
