from pydantic import BaseModel

from schorle.app import Schorle
from schorle.elements.button import Button
from schorle.elements.html import Attribute, Page, Paragraph

app = Schorle()


class State(BaseModel):
    counter: int = 0

    def increment(self):
        self.counter += 1

    def decrement(self):
        self.counter -= 1


class PageWithButton(Page):
    state: State = State()
    # hx_swap: str = Attribute(default="morph:innerHTML", alias="hx-swap")
    classes: str = "space-y-4 h-screen flex flex-col justify-center items-center"
    increment_button: Button.provide(text="Increment", classes="btn btn-primary")
    decrement_button: Button.provide(text="Decrement", classes="btn btn-secondary", disabled=True)
    counter_view: Paragraph.provide()

    @property
    def message(self):
        return f"Clicked {self.state.counter} times"

    def __init__(self, **data):
        super().__init__(**data)
        self.increment_button.set_callback(self._inc)
        self.decrement_button.set_callback(self._dec)
        self.counter_view.text = self.message

    async def _inc(self):
        self.state.increment()
        self.counter_view.text = self.message
        if self.state.counter > 0:
            self.decrement_button.enable()
        await self.update()

    async def _dec(self):
        self.state.decrement()
        self.counter_view.text = self.message
        if self.state.counter <= 0:
            self.decrement_button.disable()
        await self.update()


@app.get("/")
def index():
    page = PageWithButton()
    return page
