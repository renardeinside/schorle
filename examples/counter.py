from schorle.elements.classes import Classes
from schorle.elements.page import Page
from schorle.elements.button import Button
from schorle.app import Schorle

app = Schorle()


class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1


class AppState:
    counter: Counter = Counter()


class ButtonWithCounter(Button):

    async def on_click(self, counter: Counter = Effects(AppState.counter)):
        counter.increment()
        await self.text.update(f"Clicked {counter.count} times")


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen bg-gray-100")
    button: Button = Button(text="Click me!")


@app.get("/")
def get_page():
    return PageWithButton()
