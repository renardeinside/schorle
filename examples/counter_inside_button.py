from schorle.app import Schorle
from schorle.elements.base import ObservableModel
from schorle.elements.button import Button
from schorle.elements.page import Page
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


class State(ObservableModel):
    counter: int = 0

    def increment(self):
        self.counter += 1


class ButtonWithState(Button):
    state: State = State()

    def __init__(self, **data):
        super().__init__(**data)
        self.set_callback(self.state.increment)
        self.bind(
            self.state,
            lambda s: self.update_text(f"Counter: {s.counter}"),
            on_load=True,
        )


class PageWithButton(Page):
    classes: str = "h-screen flex flex-col justify-center items-center"
    btn: ButtonWithState.provide(text="Increment", classes="btn btn-primary")


@app.get("/")
def index():
    page = PageWithButton()
    return page
