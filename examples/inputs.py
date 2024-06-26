from contextlib import contextmanager

from schorle.app import Schorle
from schorle.attrs import Bind, On
from schorle.component import component
from schorle.element import button, div, h2, input_
from schorle.signal import Signal
from schorle.store import Depends, store
from schorle.text import text
from schorle.theme import Theme

app = Schorle(title="Schorle | IO Examples", theme=Theme.DARK)

input_store = store("", scope="component")


@component()
def simple_input(state: Signal[str] = Depends(input_store)):
    input_(
        type="text",
        placeholder="Enter your name",
        bind=Bind("value", state),
        classes="input input-primary w-full",
    )
    with div(classes="text-center m-2"):
        text(f"Hello, {state()}!") if state() else text("Hello, stranger!")


@component(classes="flex justify-around")
def clearable_input(state: Signal[str] = Depends(input_store)):
    input_(
        type="text",
        placeholder="Enter something here",
        bind=Bind("value", state),
        classes="input input-primary",
    )
    with button(on=On("click", state.partial("")), classes="btn btn-primary"):
        text("Clear")


@contextmanager
def card(title: str):
    with div(classes="card w-96 bg-base-300 shadow-xl"):
        with div(classes="card-body"):
            with h2(classes="card-title"):
                text(title)
            yield


@component(tag="main", classes="flex flex-col items-center justify-center h-screen space-y-4")
def examples_view():
    with card("Simple Input"):
        simple_input()
    with card("Clearable Input"):
        clearable_input()


@app.get("/")
def home():
    return examples_view()
