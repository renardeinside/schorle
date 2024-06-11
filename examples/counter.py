from functools import partial

from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import component
from schorle.element import button
from schorle.signal import Signal
from schorle.store import Depends, store
from schorle.text import text

app = Schorle(title="Schorle | Counter App")


@store(scope="session")
def counter() -> Signal[int]:
    return Signal(0)


async def increment(s: Signal[int]):
    await s.update(s() + 1)


@component()
def basic_btn(text_prefix: str, cnt: Signal[int] = Depends(counter)):
    with button(on=On("click", partial(increment, cnt)), classes="btn btn-primary"):
        text(f"{text_prefix}: {cnt()}")


@component(classes="flex flex-col items-center justify-center h-screen space-y-2")
def main_view():
    basic_btn(text_prefix="This counter")
    basic_btn(text_prefix="That counter")


@app.get("/")
def index():
    return main_view()
