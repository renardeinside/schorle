import asyncio
from functools import partial

from schorle.app import Schorle
from schorle.attrs import Bind, On, when
from schorle.component import component
from schorle.element import button, div, input_
from schorle.icon import icon
from schorle.signal import Signal
from schorle.store import Depends, signal_provider
from schorle.text import text

app = Schorle(title="Schorle | Todo App")

current_store = signal_provider("", scope="session")
loading_store = signal_provider(False, scope="session")
todos_store = signal_provider(["Buy milk", "Walk the dog", "Do laundry"], scope="session")


async def add(current: Signal[str], todos: Signal[list[str]], loading: Signal[bool]):
    if current():
        _current = current()
        await current.update("")
        async with loading.ctx(True):
            await asyncio.sleep(1)  # Simulate network request
            await todos.update([*todos(), _current])


async def remove(index: int, todos: Signal[list[str]], loading: Signal[bool]):
    async with loading.ctx(True):
        await asyncio.sleep(1)  # Simulate network request
        await todos.update([*todos()[:index], *todos()[index + 1 :]], skip_notify=True)


@component()
def add_button(
    current: Signal[str] = Depends(current_store),
    todos: Signal[list[str]] = Depends(todos_store),
    loading: Signal[bool] = Depends(loading_store),
):
    with button(
        on=On("click", partial(add, current=current, todos=todos, loading=loading)),
        classes=[
            "btn btn-primary btn-square btn-outline",
            when(current() == "").then("btn-disabled"),
        ],
    ):
        icon(name="list-plus")


@component()
def inputs(current: Signal[str] = Depends(current_store)):
    with div(classes="flex space-x-4 mb-4"):
        input_(
            classes="input input-primary grow",
            placeholder="Enter todo...",
            bind=Bind("value", current),
        )
        add_button()


@component()
def todos_view(loading: Signal[bool] = Depends(loading_store), todos: Signal[list[str]] = Depends(todos_store)):
    with div(classes="flex flex-col space-y-2"):
        if loading():
            with div(classes="flex grow items-center justify-center"):
                div(classes="loading loading-md text-primary")
        else:
            for index, todo in enumerate(todos()):
                with div(classes="flex space-x-4 items-center"):
                    with div(classes="text-lg grow"):
                        text(todo)
                    with button(
                        on=On("click", partial(remove, index=index, todos=todos, loading=loading)),
                        classes="btn btn-square btn-outline btn-success",
                    ):
                        icon(name="check")


@component(classes="flex flex-col items-center justify-center h-screen space-y-4")
def index_view():
    with div(classes="flex flex-col space-y-2"):
        inputs()
        todos_view()


@app.get("/")
def home():
    return index_view()
