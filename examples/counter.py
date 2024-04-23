import asyncio
from random import random

from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import Component
from schorle.element import button, div
from schorle.reactive import Reactive
from schorle.text import text

app = Schorle(title="Schorle | Counter App")


class CounterState(BaseModel):
    value: Reactive[int] = Field(default_factory=Reactive.factory(0))
    loading: Reactive[bool] = Field(default_factory=Reactive.factory(False))

    async def increment(self):
        async with self.loading.ctx(True):
            await asyncio.sleep(random() * 3)  # Simulate network request
            await self.value.set(self.value.rx + 1)

    async def decrement(self):
        async with self.loading.ctx(True):
            await asyncio.sleep(random() * 3)  # Simulate network request
            await self.value.set(self.value.rx - 1)


class Counter(Component):
    state: CounterState = Field(default_factory=CounterState)
    classes: str = "rounded-lg shadow-md m-4 w-80 h-32 flex flex-col items-center justify-center"

    def initialize(self):
        self.state.value.subscribe(self.rerender)
        self.state.loading.subscribe(self.rerender)

    def render(self):
        if self.state.loading.rx:
            div(classes="w-full h-full flex skeleton")
        else:
            with div(classes="space-x-4"):
                with button(on=On("click", self.state.increment), classes="btn btn-primary"):
                    text("Increment")
                with button(
                    on=On("click", self.state.decrement),
                    classes="btn btn-secondary" if self.state.value.rx > 0 else "btn btn-secondary btn-disabled",
                ):
                    text("Decrement")
            with div(classes="text-lg font-semibold text-center m-2"):
                text(f"Clicked {self.state.value.rx} times")


class HomePage(Component):
    classes: str = "flex flex-col items-center justify-center h-screen"

    def render(self):
        Counter()


@app.get("/")
def home():
    return HomePage()
