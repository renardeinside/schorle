from pydantic import BaseModel

from schorle.app import Schorle
from schorle.elements.button import Button
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


@app.state
class AppState(State):
    counter: Counter = Counter()


class ButtonWithCounter(Button):
    @reactive("click")
    async def on_click(self, c: Counter = Uses[AppState.counter]):
        c.increment()

    async def _(self, c: Counter = Depends[AppState.counter]):
        await self.text.update(f"Clicked {c.value} times")

    async def __(self, _: Counter = Depends[AppState.counter]):
        await self.classes.toggle("btn-success")


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    button: ButtonWithCounter = ButtonWithCounter(text=Text("Click me!"))

    @reactive("load once throttle:500ms")
    async def on_load(self):
        print("loaded")


@app.get("/")
def get_page():
    return PageWithButton()


if __name__ == "__main__":
    p = get_page()
    print(p.render())
