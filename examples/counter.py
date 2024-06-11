from functools import partial

from loguru import logger

from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import component
from schorle.element import button
from schorle.signal import Signal
from schorle.store import store, Depends
from schorle.text import text

app = Schorle(title="Schorle | Counter App")


@store(scope="component")
def counter() -> Signal[int]:
    return Signal(0)


async def increment(s: Signal[int]):
    await s.update(s() + 1)


@component(classes="flex flex-col items-center justify-center h-screen", element_id="main")
def main_view(cnt: Signal[int] = Depends(counter)):
    with button(on=On("click", partial(increment, cnt)), classes="btn btn-primary", element_id="blah"):
        text(f"Counter: {cnt()} with {cnt}")


@app.get("/")
def index():
    return main_view()
