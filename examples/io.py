from contextlib import contextmanager

from pydantic import Field

from schorle.app import Schorle
from schorle.attrs import Bind, On
from schorle.component import Component
from schorle.element import button, div, h2, input_
from schorle.reactive import Reactive
from schorle.text import text
from schorle.theme import Theme

app = Schorle(title="Schorle | IO Examples", theme=Theme.DARK)


class SimpleInput(Component):
    current: Reactive[str] = Field(default_factory=Reactive.factory(""))

    def initialize(self):
        self.current.subscribe(self.rerender)

    def render(self):
        input_(
            type="text",
            placeholder="Enter your name",
            bind=Bind("value", self.current),
            classes="input input-primary w-full",
        )
        with div(classes="text-center m-2"):
            text(f"Hello, {self.current.rx}!") if self.current.rx else text("Hello, stranger!")


class Clearable(Component):
    current: Reactive[str] = Field(default_factory=Reactive.factory(""))
    classes: str = "flex justify-around"

    def initialize(self):
        self.current.subscribe(self.rerender)

    def render(self):
        input_(
            type="text",
            placeholder="Enter something here",
            bind=Bind("value", self.current),
            classes="input input-primary",
        )
        with button(on=On("click", self.current.lazy("")), classes="btn btn-primary"):
            text("Clear")


class Examples(Component):
    tag: str = "main"
    classes: str = "flex flex-col items-center justify-center h-screen space-y-4"

    @staticmethod
    @contextmanager
    def card(title: str):
        with div(classes="card w-96 bg-base-300 shadow-xl"):
            with div(classes="card-body"):
                with h2(classes="card-title"):
                    text(title)
                yield

    def render(self):
        with self.card("Simple Input"):
            SimpleInput()
        with self.card("Clearable Input"):
            Clearable()


@app.get("/")
def home():
    return Examples()
