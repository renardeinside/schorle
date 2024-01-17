from pydantic import BaseModel

from schorle.app import Schorle
from schorle.elements.button import Button
from schorle.elements.html import Div
from schorle.elements.page import Page
from schorle.observables.classes import Classes
from schorle.observables.text import Text
from schorle.state import Depends, State, Uses
from schorle.utils import reactive

app = Schorle()


class Counter(BaseModel):
    value: int = 0

    def increment(self):
        self.value += 1

    def decrement(self):
        self.value -= 1


@app.state
class AppState(State):
    counter: Counter = Counter()


class IncrementButton(Button):
    classes: Classes = Classes("btn-primary")

    @reactive("click")
    async def on_click(self, counter: Counter = Uses[AppState.counter]):
        counter.increment()


class DecrementButton(Button):
    classes: Classes = Classes("btn-secondary", "btn-disabled")

    @reactive("click")
    async def on_click(self, counter: Counter = Uses[AppState.counter]):
        counter.decrement()

    async def _(self, counter: Counter = Depends[AppState.counter]):
        if counter.value <= 0:
            await self.classes.append("btn-disabled")
        else:
            await self.classes.remove("btn-disabled")


class Buttons(Div):
    classes: Classes = Classes("space-x-4 flex flex-row justify-center items-center")
    increment_button: IncrementButton = IncrementButton(text="Increment")
    decrement_button: DecrementButton = DecrementButton(text="Decrement")


class CounterView(Div):
    text: Text = Text("Clicked 0 times")

    async def on_update(self, counter: Counter = Depends[AppState.counter]):
        await self.text.update(f"Clicked {counter.value} times")


class PageWithButton(Page):
    classes: Classes = Classes("space-y-4 flex flex-col justify-center items-center h-screen w-screen")
    buttons: Buttons = Buttons()
    counter_view: CounterView = CounterView()


@app.get("/")
def get_page():
    return PageWithButton()
