from pydantic import Field

from schorle.app import Schorle
from schorle.attrs import Bind
from schorle.component import Component
from schorle.element import div, input_, span
from schorle.reactive import Reactive
from schorle.text import text

app = Schorle()


class IOComponent(Component):
    current: Reactive[str] = Field(default_factory=Reactive.factory(""))

    def initialize(self):
        self.current.subscribe(self.rerender)

    def render(self):
        with div():
            input_(type="text", placeholder="Enter your name", bind=Bind("value", self.current))
        with span():
            text(f"Hello, {self.current.rx}!")


@app.get("/")
def home():
    return IOComponent()
