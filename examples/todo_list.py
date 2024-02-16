from functools import partial

from pydantic import Field

from schorle.app import Schorle
from schorle.button import Button
from schorle.classes import Classes
from schorle.effector import effector
from schorle.element import div, p
from schorle.inputs import TextInput
from schorle.on import On
from schorle.page import Page
from schorle.state import ReactiveModel
from schorle.text import text

app = Schorle()


class State(ReactiveModel):
    current: str = ""
    todos: list[str] = Field(default_factory=lambda: ["Buy milk", "Do laundry"])

    @effector
    def set_current(self, value):
        self.current = value

    @effector
    def add_todo(self):
        self.todos.append(self.current)
        self.set_current("")

    @effector
    def remove(self, todo):
        self.todos.remove(todo)


class TodoListPage(Page):
    state: State = State.factory()

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            with div(classes=Classes("flex flex-row w-3/4 justify-center items-center space-x-4")):
                TextInput(
                    value=self.state.current,
                    placeholder="Add a todo",
                    classes=Classes("input-bordered"),
                    on=On("change", self.state.set_current),
                )
                with Button(on=On("click", self.state.add_todo), modifier="primary"):
                    text("Add")

            with div(classes=Classes("flex flex-col justify-center items-center space-y-2 w-48 md:w-96 m-4")):
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
        self.bind(self.state)


@app.get("/")
def index():
    return TodoListPage()
