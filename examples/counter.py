from schorle.app import Schorle
from schorle.elements.base import ObservableModel
from schorle.elements.button import Button
from schorle.elements.html import Div, Paragraph
from schorle.elements.page import Page
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


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
    counter: Paragraph.provide(text="Counter: 0", classes="text-6xl")


@app.get("/")
def index():
    state = State()
    page = PageWithButton()

    page.buttons.inc.set_callback(state.increment)
    page.buttons.dec.set_callback(state.decrement)
    page.counter.bind(state, lambda s: page.counter.update_text(f"Counter: {s.counter}"))
    page.buttons.dec.bind(state, lambda s: page.buttons.dec.disable() if s.counter <= 0 else page.buttons.dec.enable())
    return page
