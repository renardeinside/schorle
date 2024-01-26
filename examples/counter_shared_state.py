from __future__ import annotations

from schorle.app import Schorle
from schorle.effector import effector
from schorle.elements.button import Button
from schorle.elements.html import Div
from schorle.elements.page import Page, PageReference
from schorle.reactives.classes import Classes
from schorle.reactives.state import ReactiveModel
from schorle.reactives.text import Text

app = Schorle()


class Counter(ReactiveModel):
    value: int = 0

    @effector
    async def increment(self):
        self.value += 1

    @effector
    async def decrement(self):
        self.value -= 1


class DecrementButton(Button):
    text: Text = Text("Decrement")
    page: PageWithButton = PageReference()
    classes: Classes = Classes("btn-error")

    async def before_render(self):
        await self.page.counter.decrement.subscribe(self._switch_off, trigger=True)
        await self.page.counter.increment.subscribe(self._switch_off, trigger=True)

    async def _switch_off(self, counter: Counter):
        if counter.value <= 0:
            await self.classes.append("btn-disabled")
        else:
            await self.classes.remove("btn-disabled")


class Buttons(Div):
    classes: Classes = Classes("space-x-4 flex flex-row justify-center items-center")
    increment: Button = Button.factory(text=Text("Increment"), classes=Classes("btn-success"))
    decrement: DecrementButton = DecrementButton.factory()
    page: PageWithButton = PageReference()

    async def before_render(self):
        self.increment.add_callback("click", self.page.counter.increment)
        self.decrement.add_callback("click", self.page.counter.decrement)


class CounterView(Div):
    page: PageWithButton = PageReference()

    async def update(self, counter: Counter):
        await self.text.update(f"Clicked {counter.value} times")

    async def before_render(self):
        await self.page.counter.increment.subscribe(self.update, trigger=True)
        await self.page.counter.decrement.subscribe(self.update, trigger=True)


class PageWithButton(Page):
    counter: Counter = Counter.factory()
    classes: Classes = Classes("space-y-4 flex flex-col justify-center items-center h-screen w-screen")
    buttons: Buttons = Buttons.factory()
    counter_view: CounterView = CounterView.factory()


@app.get("/")
def get_page():
    return PageWithButton()
