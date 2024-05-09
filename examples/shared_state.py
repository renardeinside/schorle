from typing import ClassVar

from dependency_injector.wiring import Provide

from schorle.app import Schorle
from schorle.attrs import Bind
from schorle.component import Component
from schorle.element import div, input_
from schorle.signal import Signal
from schorle.store import Store
from schorle.text import text

app = Schorle()


class InputStore(Store):
    current = Signal.shared("")


app.stores = [InputStore]


class Input(Component):
    current: ClassVar[Signal] = Provide[InputStore.current]

    def render(self):
        input_(
            type="text",
            placeholder="Enter your name",
            bind=Bind("value", self.current),
            classes="input input-primary w-full",
        )


class View(Component):
    current: ClassVar[Signal] = Provide[InputStore.current]

    def initialize(self):
        self.current.subscribe(self.rerender)

    def render(self):
        with div(classes="text-center m-2"):
            text(f"Hello, {self.current.val}!") if self.current.val else text("Hello, stranger!")


for store in app.stores:
    instance = store()
    instance.wire(modules=[__name__])


class Main(Component):
    classes: str = "flex flex-col items-center justify-center h-screen space-y-4"

    def render(self):
        Input()
        View()


@app.get("/")
def index():
    return Main()
