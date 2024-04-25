import asyncio
from functools import partial

from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.attrs import Bind, On
from schorle.component import Component
from schorle.element import button, div, input_
from schorle.icon import icon
from schorle.reactive import Reactive
from schorle.text import text

app = Schorle(title="Schorle | Todo App")


class TodoState(BaseModel):
    current: Reactive[str] = Field(default_factory=Reactive.factory(""))
    loading: Reactive[bool] = Field(default_factory=Reactive.factory(False))
    todos: Reactive[list[str]] = Field(
        default_factory=Reactive.factory(
            [
                "Buy groceries",
                "Walk the dog",
            ]
        )
    )

    async def add(self):
        if self.current.rx:
            _current = self.current.rx
            await self.current.set("")  # Clear input field
            async with self.loading.ctx(True):
                await asyncio.sleep(1)  # Simulate network request
                await self.todos.set([*self.todos.rx, _current])

    async def remove(self, index: int):
        async with self.loading.ctx(True):
            await asyncio.sleep(1)  # Simulate network request
            await self.todos.set([*self.todos.rx[:index], *self.todos.rx[index + 1 :]], skip_notify=True)


class Todos(Component):
    state: TodoState = Field(default_factory=TodoState)

    def initialize(self):
        self.state.current.subscribe(self.rerender)
        self.state.todos.subscribe(self.rerender)
        self.state.loading.subscribe(self.rerender)

    def render(self):
        with div(classes="flex flex-col space-y-2"):
            with div(classes="flex space-x-4 mb-4"):
                input_(
                    classes="input input-primary grow",
                    placeholder="Enter todo...",
                    bind=Bind("value", self.state.current),
                )
                with button(
                    on=On("click", self.state.add),
                    classes="btn btn-primary btn-square btn-outline"
                    + (" btn-disabled" if not self.state.current.rx else ""),
                ):
                    icon(name="list-plus")

        with div(classes="flex flex-col space-y-2"):

            if self.state.loading.rx:
                with div(classes="flex grow items-center justify-center"):
                    div(classes="loading loading-md text-primary")
            else:
                for index, todo in enumerate(self.state.todos.rx):
                    with div(classes="flex space-x-4 items-center"):
                        with div(classes="text-lg grow"):
                            text(todo)
                        with button(
                            on=On("click", partial(self.state.remove, index)),
                            classes="btn btn-square btn-outline btn-success",
                        ):
                            icon(name="check")


class HomePage(Component):
    classes: str = "flex flex-col items-center justify-center h-screen space-y-4"

    def render(self):
        Todos()


@app.get("/")
def home():
    return HomePage()
