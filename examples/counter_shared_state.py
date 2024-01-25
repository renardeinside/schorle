from __future__ import annotations

from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.dynamics.classes import Classes
from schorle.dynamics.text import Text
from schorle.elements.button import Button
from schorle.elements.html import Div
from schorle.elements.page import Page, PageReference
from schorle.emitter import emitter, inject_emitters
from schorle.utils import before_render

app = Schorle()


class Counter(BaseModel, extra="allow"):
    value: int = 0

    @emitter
    async def increment(self):
        self.value += 1

    @emitter
    async def decrement(self):
        self.value -= 1


class DecrementButton(Button):
    text: Text = Text("Decrement")
    page: PageWithButton = PageReference()
    classes: Classes = Classes("btn-error")

    @before_render
    async def preload(self):
        await self._switch_off(self.page.counter)
        self.page.counter.decrement.subscribe(self._switch_off)
        self.page.counter.increment.subscribe(self._switch_off)

    async def _switch_off(self, counter: Counter):
        if counter.value <= 0:
            await self.classes.append("btn-disabled")
        else:
            await self.classes.remove("btn-disabled")


class Buttons(Div):
    classes: Classes = Classes("space-x-4 flex flex-row justify-center items-center")
    increment: Button = Field(default_factory=lambda: Button(text=Text("Increment"), classes=Classes("btn-success")))
    decrement: Button = Field(default_factory=DecrementButton)


class CounterView(Div):
    page: PageWithButton = PageReference()

    async def update(self, counter: Counter):
        await self.text.update(f"Clicked {counter.value} times")

    @before_render
    async def preload(self):
        await self.update(self.page.counter)
        self.page.counter.increment.subscribe(self.update)
        self.page.counter.decrement.subscribe(self.update)


class PageWithButton(Page):
    counter: Counter = Counter()
    classes: Classes = Classes("space-y-4 flex flex-col justify-center items-center h-screen w-screen")
    buttons: Buttons = Field(default_factory=Buttons)
    counter_view: CounterView = Field(default_factory=CounterView)

    def __init__(self, **data):
        super().__init__(**data)
        inject_emitters(self.counter)
        self.buttons.increment.add_callback("click", self.counter.increment)
        self.buttons.decrement.add_callback("click", self.counter.decrement)


@app.get("/")
def get_page():
    return PageWithButton()
