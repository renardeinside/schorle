import asyncio

from loguru import logger

from schorle.app import Schorle
from schorle.elements.base import ObservableModel
from schorle.elements.button import Button
from schorle.elements.page import Page
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


class State(ObservableModel):
    counter: int = 0

    def increment(self):
        logger.info("incrementing")
        self.counter += 1


class ButtonWithState(Button):
    state: State = State()

    def __init__(self, **data):
        super().__init__(**data)
        self.set_callback(self.state.increment)
        self.bind(self.state, self.on_update, on_load=True)

    async def on_update(self, state: State):
        with self.suspend():
            await asyncio.sleep(2 + self.state.counter * 0.1)

        self.update_text(f"Counter: {state.counter}")


class PageWithButton(Page):
    classes: str = "gap-2 h-screen flex flex-col justify-center items-center"
    btn1: ButtonWithState.provide(text="Increment", classes="btn btn-primary w-2/12")
    btn2: ButtonWithState.provide(text="Increment", classes="btn btn-primary w-2/12")
    btn3: ButtonWithState.provide(text="Increment", classes="btn btn-primary w-2/12")


@app.get("/")
def index():
    page = PageWithButton()
    return page
