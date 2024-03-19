from __future__ import annotations

from functools import partial
from typing import Annotated

from fastapi import Form
from loguru import logger

from schorle.app import Schorle
from schorle.attrs import Classes, Reactive, Swap, delete, post
from schorle.controller import render
from schorle.element import button, div, form, input_, span
from schorle.icon import icon
from schorle.text import text
from schorle.theme import Theme
from schorle.utils import empty

app = Schorle(theme=Theme.DARK)


def task_view(task: str):
    with div(Classes("flex flex-row justify-between items-center w-full")):
        with span():
            text(task)
        with button(
            classes=Classes("btn btn-error btn-square"),
            reactive=Reactive(delete(f"/delete?task={task}"), "closest div"),
        ):
            icon("trash")


def task_input():
    with form(
        Classes("flex flex-row justify-center items-center w-96 space-x-2"),
        reactive=Reactive(post("/add"), "#tasks", Swap.before_end),
        hsx="""
                on htmx:beforeRequest
                    add .btn-disabled to #add-button
                on htmx:afterRequest
                    if event.detail.successful
                    my.reset()
                    """,
    ):
        input_(
            placeholder="What needs to be done?",
            name="task",
            classes=Classes("input input-primary w-96"),
            hsx="""
                on keyup
                    if event.key is 'Escape' set my value to '' trigger keyup
                    else
                        if my.value.length > 0 remove .btn-disabled from #add-button
                        else add .btn-disabled to #add-button
               """,
        )
        with button(
            Classes("btn btn-primary btn-square btn-disabled"),
            element_id="add-button",
        ):
            icon("plus")


def tasks_view():
    with div(Classes("flex flex-col justify-center items-center w-96 space-y-2 mt-2"), element_id="tasks"):
        for task in app.backend.state.tasks:
            task_view(task)


def main_view():
    with div(Classes("flex flex-col justify-center items-center h-screen")):
        task_input()
        tasks_view()


@app.backend.get("/")
def home():
    app.backend.state.tasks = ["task 1", "task 2", "task 3"]
    return app.doc.render(main_view)


@app.backend.post("/add")
def add(task: Annotated[str, Form()]):
    logger.info(f"Adding task: {task}")
    app.backend.state.tasks.append(task)
    return render(partial(task_view, task))


@app.backend.delete("/delete")
def delete_task(task: str):
    logger.info(f"Deleting task: {task}")
    app.backend.state.tasks.remove(task)
    return empty()
