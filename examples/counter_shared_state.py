from schorle.elements.classes import Classes
from schorle.elements.html import Div
from schorle.elements.page import Page
from schorle.elements.button import Button
from schorle.app import Schorle
from dependency_injector.wiring import Provide
app = Schorle()


class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

@app.state
class State:
    counter: Counter = Counter()


class IncrementButton(Button):

    async def on_click(self, counter: Counter = Uses[State.counter]):
        counter.increment()


class DecrementButton(Button):

    async def on_click(self, counter: Counter = Provide[State.counter]):
        counter.decrement()

    async def on_update(self, counter: Counter = Depends[State.counter]):
        if counter.count < 0:
            await self.disable()
        else:
            await self.enable()


class CounterView(Div):
    text: Text = Text("Clicked 0 times")

    async def on_update(self, counter: Counter = Depends[AppState.counter]):
        await self.text.update(f"Clicked {counter.count} times")


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen bg-gray-100")
    button: Button = Button(text="Click me!")
    counter_view: CounterView = CounterView()


@app.get("/")
def get_page():
    return PageWithButton()
