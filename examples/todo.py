import asyncio
from functools import partial

from pydantic import BaseModel

from schorle.app import Schorle
from schorle.attrs import Bind, On, when
from schorle.component import component
from schorle.element import button, div, input_
from schorle.icon import icon
from schorle.reactive import Reactive
from schorle.session import Session
from schorle.text import text

app = Schorle(title="Schorle | Todo App")


class TodoState(BaseModel):
    current: Reactive[str] = Reactive.field("")
    loading: Reactive[bool] = Reactive.field(False)
    todos: Reactive[list[str]] = Reactive.field(["Buy milk", "Walk the dog", "Do laundry"])

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


@app.session_state
def session_state():
    return TodoState()


@component()
def inputs(session: Session[TodoState]):
    with div(classes="flex space-x-4 mb-4"):
        input_(
            classes="input input-primary grow",
            placeholder="Enter todo...",
            bind=Bind("value", session.state.current),
        )
        with button(
            on=On("click", session.state.add),
            classes=[
                "btn btn-primary btn-square btn-outline",
                when(session.state.current.rx == "").then("btn-disabled"),
            ],
        ):
            icon(name="list-plus")


@component()
def todos(session: Session[TodoState]):
    with div(classes="flex flex-col space-y-2"):

        if session.state.loading.rx:
            with div(classes="flex grow items-center justify-center"):
                div(classes="loading loading-md text-primary")
        else:
            for index, todo in enumerate(session.state.todos.rx):
                with div(classes="flex space-x-4 items-center"):
                    with div(classes="text-lg grow"):
                        text(todo)
                    with button(
                        on=On("click", partial(session.state.remove, index)),
                        classes="btn btn-square btn-outline btn-success",
                    ):
                        icon(name="check")


@component(classes="flex flex-col items-center justify-center h-screen space-y-4")
def index_view():
    with div(classes="flex flex-col space-y-2"):
        inputs()
        todos()


@app.get("/")
def home():
    return index_view()
