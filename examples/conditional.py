from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.elements.button import Button
from schorle.elements.html import Div
from schorle.elements.page import Page
from schorle.observables.base import Dynamic
from schorle.observables.classes import Classes
from schorle.observables.text import Text
from schorle.state import Depends, State, Uses
from schorle.utils import reactive

app = Schorle()


class Counter(BaseModel):
    value: int = 0


class PageState(State):
    counter: Counter = Counter()


class ButtonWithCounter(Button):
    @reactive("click")
    async def on_click(self, c: Counter = Uses[PageState.counter]):
        c.value += 1

    async def _(self, c: Counter = Depends[PageState.counter]):
        await self.text.update(f"Clicked {c.value} times")

    async def __(self, _: Counter = Depends[PageState.counter]):
        await self.classes.toggle("btn-success")


class PageWithButton(Page):
    state: PageState = PageState()
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    button: ButtonWithCounter = ButtonWithCounter(text=Text("Click me!"))
    view: Dynamic[Div] = Field(default_factory=Dynamic)

    async def _view(self, c: Counter = Depends[PageState.counter]):
        new_div = Div(text=Text("Even") if c.value % 2 == 0 else Text("Odd"), classes=Classes("text-2xl text-center"))
        if c.value % 2 == 0:
            await self.view.update(new_div)
        else:
            await self.view.update(None)


@app.get("/")
def get_page():
    return PageWithButton()
