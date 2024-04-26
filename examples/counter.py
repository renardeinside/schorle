from pydantic import Field

from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import Component
from schorle.element import button, div
from schorle.reactive import Reactive
from schorle.text import text

app = Schorle(title="Schorle | Counter App")


class Counter(Component):
    value: Reactive[int] = Field(default_factory=Reactive.factory(0))

    def initialize(self):
        self.value.subscribe(self.rerender)

    def render(self):
        with div(classes="space-x-4"):
            with button(on=On("click", self.value.lazy(self.value.rx + 1)), classes="btn btn-primary"):
                text("Increment")
        with div(classes="text-lg font-semibold text-center m-2"):
            text(f"Clicked {self.value.rx} times")


@app.get("/")
def home_page():
    return Counter()
