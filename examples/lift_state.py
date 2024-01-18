from __future__ import annotations

from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.dynamics.classes import Classes
from schorle.dynamics.text import Text
from schorle.elements.button import Button
from schorle.elements.html import Paragraph
from schorle.elements.page import Page
from schorle.state import Depends, State, Uses
from schorle.utils import reactive, before_load

app = Schorle()


class Counter(BaseModel):
    value: int = 0


class Summary(BaseModel):
    value: int = 0


class PageState(State):
    summary: Summary = Summary()


class ButtonWithCounter(Button):
    counter: Counter = Field(default_factory=Counter)

    @reactive("click")
    async def on_click(self, summary: Summary = Uses[PageState.summary]):
        self.counter.value += 1
        summary.value += 1


class TotalView(Paragraph):
    @before_load()
    async def on_update(self, summary: Summary = Depends[PageState.summary]):
        await self.text.update(f"Total: {summary.value}")


class PageWithButton(Page):
    state: PageState = PageState()
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    first_button: ButtonWithCounter = ButtonWithCounter(text=Text("Click me!"))
    second_button: ButtonWithCounter = ButtonWithCounter(text=Text("Click me too!"))
    total_view: TotalView = Field(default_factory=TotalView)


@app.get("/")
def get_page():
    return PageWithButton()
