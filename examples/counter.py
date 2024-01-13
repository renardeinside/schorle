from random import randint

from schorle.app import Schorle
from schorle.elements.button import Button
from schorle.elements.classes import Classes
from schorle.elements.page import Page

app = Schorle()


class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1


class AppState:
    counter: Counter = Counter()


class ButtonWithCounter(Button):
    async def on_click(self):
        self.text = f"hey {randint(0, 100)}"
        self.classes.toggle("btn-primary")


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    button: ButtonWithCounter = ButtonWithCounter(text="Click me!")


@app.get("/")
def get_page():
    return PageWithButton()
