import asyncio
from contextlib import contextmanager
from random import random

from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.attrs import On, when
from schorle.component import component
from schorle.element import button, div
from schorle.reactive import Reactive
from schorle.text import text

app = Schorle(title="Schorle | Counter App")


class CounterState(BaseModel):
    value: Reactive[int] = Field(default_factory=Reactive.factory(1))
    loading: Reactive[bool] = Field(default_factory=Reactive.factory(False))

    async def increment(self):
        async with self.loading.ctx(True):
            await asyncio.sleep(random() * 3)  # Simulate network request
            await self.value.set(self.value.rx + 1, skip_notify=True)

    async def decrement(self):
        async with self.loading.ctx(True):
            await asyncio.sleep(random() * 3)  # Simulate network request
            await self.value.set(self.value.rx - 1, skip_notify=True)


@contextmanager
def spinner(loading: Reactive[bool]):
    with div(classes=when(loading).then("loading loading-infinity loading-lg text-primary")):
        with div(classes=when(loading).then("hidden")):
            yield


@component(
    classes="m-4 w-80 h-32 flex flex-col items-center justify-center bg-base-300 rounded-xl shadow-xl",
    state=lambda: CounterState(),
)
def counter_with_loading(state: CounterState):
    with spinner(state.loading):
        with div(classes="space-x-4"):
            with button(on=On("click", state.increment), classes="btn btn-primary"):
                text("Increment")
            with button(
                on=On("click", state.decrement),
                classes=["btn btn-secondary", when(state.value.rx == 0).then("btn-disabled")],
            ):
                text("Decrement")
        with div(classes="text-lg font-semibold text-center m-2"):
            text(f"Clicked {state.value.rx} times")


@component(classes="flex flex-col items-center justify-center h-screen")
def index_view():
    counter_with_loading()


@app.get("/")
def home():
    return index_view()
