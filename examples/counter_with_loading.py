import asyncio
from contextlib import contextmanager
from functools import partial
from random import random

from schorle.app import Schorle
from schorle.attrs import On, when
from schorle.component import component
from schorle.element import button, div
from schorle.signal import Signal
from schorle.store import Depends, store
from schorle.text import text

app = Schorle(title="Schorle | Counter App")

value_store = store(0, scope="component")
loading_store = store(False, scope="component")


async def step(loading: Signal[bool], value: Signal[int], action: callable):
    async with loading.ctx(True):
        await asyncio.sleep(random() * 3)  # Simulate network request
        await value.update(action(value(), 1), skip_notify=True)


increment = partial(step, action=lambda x, y: x + y)
decrement = partial(step, action=lambda x, y: x - y)


@contextmanager
def spinner(loading: Signal[bool]):
    with div(classes=when(loading).then("loading loading-infinity loading-lg text-primary")):
        with div(classes=when(loading).then("hidden")):
            yield


@component(
    classes="m-4 w-80 h-32 flex flex-col items-center justify-center bg-base-300 rounded-xl shadow-xl",
)
def counter_with_loading(loading: Signal[bool] = Depends(loading_store), value: Signal[int] = Depends(value_store)):
    with spinner(loading):
        with div(classes="space-x-4"):
            with button(on=On("click", partial(increment, value=value, loading=loading)), classes="btn btn-primary"):
                text("Increment")
            with button(
                on=On("click", partial(decrement, value=value, loading=loading)),
                classes=["btn btn-secondary", when(value() == 0).then("btn-disabled")],
            ):
                text("Decrement")
        with div(classes="text-lg font-semibold text-center m-2"):
            text(f"Clicked {value()} times")


@component(classes="flex flex-col items-center justify-center h-screen")
def index_view():
    counter_with_loading()
    counter_with_loading()


@app.get("/")
def home():
    return index_view()
