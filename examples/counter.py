from pydantic import BaseModel

from schorle.app import Schorle
from schorle.elements.button import ReactiveButton
from schorle.elements.page import Page
from schorle.observables.classes import Classes
from schorle.observables.text import Text
from schorle.state import Depends, State, Uses

app = Schorle()


class Counter(BaseModel):
    value: int = 0

    def increment(self):
        self.value += 1


@app.state
class AppState(State):
    counter: Counter = Counter()


class ButtonWithCounter(ReactiveButton):
    async def on_click(self, c: Counter = Uses[AppState.counter]):
        c.increment()

    async def _(self, c: Counter = Depends[AppState.counter]):
        await self.text.update(f"Clicked {c.value} times")

    async def __(self, _: Counter = Depends[AppState.counter]):
        await self.classes.toggle("btn-success")


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    button: ButtonWithCounter = ButtonWithCounter(text=Text("Click me!"))


@app.get("/")
def get_page():
    return PageWithButton()
