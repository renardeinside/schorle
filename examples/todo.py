import asyncio

from pydantic import BaseModel

from schorle.app import Schorle
from schorle.attrs import On, when
from schorle.component import Component
from schorle.element import button, div
from schorle.icon import icon
from schorle.signal import Signal

app = Schorle(title="Schorle | Todo App")


class TodoState(BaseModel):
    current: Signal[str] = Signal.field("")
    loading: Signal[bool] = Signal.field(False)
    todos: Signal[list[str]] = Signal.field(["Buy milk", "Walk the dog", "Do laundry"])

    async def add(self):
        if self.current.val:
            _current = self.current.val
            await self.current.set("")  # Clear input field
            async with self.loading.ctx(True):
                await asyncio.sleep(1)  # Simulate network request
                await self.todos.set([*self.todos.val, _current])

    async def remove(self, index: int):
        async with self.loading.ctx(True):
            await asyncio.sleep(1)  # Simulate network request
            await self.todos.set([*self.todos.val[:index], *self.todos.val[index + 1 :]], skip_notify=True)


@app.session_state
def todo_state():
    return TodoState()


class InputSection(Component):

    def initialize(self, state: TodoState = Depends(todo_state)):
        state.current.subscribe(self.rerender)

    def render(self, state: TodoState = Depends(todo_state)):
        with button(
            on=On("click", state.add),
            classes=[
                "btn btn-primary btn-square btn-outline",
                when(state.current.val == "").then("btn-disabled"),
            ],
        ):
            icon(name="list-plus")


@component()
def inputs(session: Session[TodoState]):
    with div(classes="flex space-x-4 mb-4"):
        input_(
            classes="input input-primary grow",
            placeholder="Enter todo...",
            bind=Bind("value", session.state.current),
        )
        add_button()


#
#
# @component()
# def todos(session: Session[TodoState]):
#     with div(classes="flex flex-col space-y-2"):
#
#         if session.state.loading.rx:
#             with div(classes="flex grow items-center justify-center"):
#                 div(classes="loading loading-md text-primary")
#         else:
#             for index, todo in enumerate(session.state.todos.rx):
#                 with div(classes="flex space-x-4 items-center"):
#                     with div(classes="text-lg grow"):
#                         text(todo)
#                     with button(
#                             on=On("click", partial(session.state.remove, index)),
#                             classes="btn btn-square btn-outline btn-success",
#                     ):
#                         icon(name="check")
#
#


class MainView(Component):
    classes: str = "flex flex-col items-center justify-center h-screen space-y-4"
    tag: str = "main"

    def render(self):
        with div(classes="flex flex-col space-y-2"):
            InputSection()


@app.get("/")
def home():
    return MainView()
