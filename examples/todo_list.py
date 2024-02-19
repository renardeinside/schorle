import asyncio
from functools import partial
from random import random

from pydantic import Field

from schorle.app import Schorle
from schorle.button import Button
from schorle.classes import Classes
from schorle.component import Component
from schorle.effector import effector
from schorle.element import div, p
from schorle.inputs import TextInput
from schorle.loading import Loading
from schorle.on import On
from schorle.page import Page
from schorle.state import ReactiveModel
from schorle.suspense import Suspense
from schorle.text import text

app = Schorle()


class State(ReactiveModel):
    current: str = ""
    todos: list[str] = Field(default_factory=lambda: ["Buy milk", "Do laundry"])

    @effector
    async def set_current(self, value):
        self.current = value

    @effector
    async def add_todo(self):
        await asyncio.sleep(random() * 2)  # Simulate a slow network request
        self.todos.append(self.current)
        await self.set_current("")

    @effector
    async def remove(self, todo):
        await asyncio.sleep(random() * 2)  # Simulate a slow network request
        self.todos.remove(todo)


class InputSection(Component):
    state: State
    classes: Classes = Classes("flex flex-row w-3/4 justify-center items-center space-x-4")

    def render(self):
        TextInput(
            value=self.state.current,
            placeholder="Add a todo",
            classes=Classes("input-bordered"),
            on=On("change", self.state.set_current),
        )
        with Button(on=On("click", self.state.add_todo), modifier="primary"):
            text("Add")

    def initialize(self):
        self.bind(self.state)


class TodoView(Component):
    state: State
    classes: Classes = Classes(
        "max-w-xl w-2/3 space-y-2 flex flex-col items-center h-96 m-4 shadow-lg p-10 rounded-lg bg-base-300"
    )

    def render(self):
        with p(classes=Classes("text-xl")):
            _text = "No todos yet." if not self.state.todos else "Your todos:"
            text(_text)

        for todo in self.state.todos:
            with div(classes=Classes("flex flex-row items-center justify-between w-full")):
                with p():
                    text(todo)
                with Button(
                    on=On("click", partial(self.state.remove, todo)),
                    modifier="error",
                ):
                    text("Delete")

    def initialize(self):
        self.suspense = Suspense(on=self.state, fallback=Loading())
        self.bind(self.state)


class TodoListPage(Page):
    state: State = State.factory()
    classes: Classes = Classes("m-4 flex flex-col items-center h-screen")

    def render(self):
        InputSection(state=self.state)
        TodoView(state=self.state)


@app.get("/")
def index():
    return TodoListPage()
