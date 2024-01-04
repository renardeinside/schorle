from schorle.app import Schorle
from schorle.elements.base import ObservableModel
from schorle.elements.button import Button
from schorle.elements.html import Div, Paragraph
from schorle.elements.page import Page

app = Schorle()


class State(ObservableModel):
    counter: int = 0

    def increment(self):
        self.counter += 1

    def decrement(self):
        self.counter -= 1


class Buttons(Div):
    classes: str = "space-x-4"
    inc: Button.provide(text="Increment", classes="btn btn-primary")
    dec: Button.provide(text="Decrement", classes="btn btn-secondary")


class PageWithButton(Page):
    classes: str = "space-y-4 h-screen flex flex-col justify-center items-center"
    buttons: Buttons.provide()
    counter_view: Paragraph.provide(classes="text-6xl")


@app.get("/")
def index():
    state = State()
    page = PageWithButton()

    async def _inc():
        state.increment()
        page.counter_view.text = f"Counter: {state.counter}"
        if state.counter > 0:
            page.buttons.dec.enable()

    async def _dec():
        state.decrement()
        page.counter_view.text = f"Counter: {state.counter}"
        if state.counter <= 0:
            page.buttons.dec.disable()

    page.buttons.inc.set_callback(_inc)
    page.buttons.dec.set_callback(_dec)
    return page
