from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import component
from schorle.element import button, div
from schorle.reactive import Reactive
from schorle.text import text

app = Schorle(title="Schorle | Counter App")


@component(state=Reactive.factory(0))
def counter(state: Reactive[int]):
    with div(classes="flex flex-col items-center"):
        with button(classes="btn btn-primary", on=On("click", state.lazy(state.rx + 1))):
            text("Increment")
        with div(classes="text-lg font-semibold text-center m-2"):
            text(f"Clicked {state.rx} times")


@component(classes="flex flex-col items-center justify-center h-screen")
def index_view():
    counter()
    counter()


@app.get("/")
def index():
    return index_view()
