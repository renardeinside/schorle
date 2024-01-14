from pydantic import BaseModel

from schorle.app import Schorle
from schorle.elements.button import Button
from schorle.elements.classes import Classes
from schorle.elements.page import Page
from schorle.state import Provide, State

app = Schorle()


class Counter(BaseModel):
    value: int = 0

    def increment(self):
        self.value += 1


@app.state
class AppState(State):
    counter: Counter = Counter()


class ButtonWithCounter(Button):
    async def on_click(self, c: Counter = Provide[AppState.counter]):
        c.increment()
        self.text = f"Clicked {c.value} times"
        self.classes.toggle("btn-primary")


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    button: ButtonWithCounter = ButtonWithCounter(text="Click me!")


@app.get("/")
def get_page():
    return PageWithButton()
