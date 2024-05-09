from dependency_injector.wiring import Provide

from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import Component
from schorle.element import button, div
from schorle.signal import Signal
from schorle.store import Store
from schorle.text import text

app = Schorle(title="Schorle | Counter App")


class CounterStore(Store):
    counter: Signal[int] = Signal.shared(0)


app.stores = [CounterStore]


class CounterView(Component):
    counter: Signal[int] = Provide[CounterStore.counter]

    def initialize(self):
        self.counter.subscribe(self.rerender)

    def render(self):
        with div(classes="flex flex-col items-center"):
            with button(classes="btn btn-primary", on=On("click", self.counter.lazy(self.counter.val + 1))):
                text("Increment")
            with div(classes="text-lg font-semibold text-center m-2"):
                text(f"Clicked {self.counter.val} times")


for store in app.stores:
    instance = store()
    instance.wire(modules=[__name__])


class MainView(Component):

    def render(self):
        CounterView()
        CounterView()


@app.get("/")
def index():
    return MainView()
