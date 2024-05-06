from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import Depends, component
from schorle.element import button, div
from schorle.signal import Signal
from schorle.text import text

app = Schorle(title="Schorle | Counter App")

counter_signal = Signal(0)


@component()
def counter(signal: Signal[int] = Depends(counter_signal)):
    with div(classes="flex flex-col items-center"):
        with button(classes="btn btn-primary", on=On("click", signal.lazy(signal.val + 1))):
            text("Increment")
        with div(classes="text-lg font-semibold text-center m-2"):
            text(f"Clicked {signal.val} times")


@component(tag="main")
def main_view():
    counter()
    counter()


@app.get("/")
def index():
    return main_view()
