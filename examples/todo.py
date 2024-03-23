from __future__ import annotations

from typing import Annotated

from fastapi import Form
from loguru import logger

from schorle.app import Schorle
from schorle.attrs import Classes, Reactive, Swap, delete, post
from schorle.element import button, div, form, input_, span
from schorle.icon import icon
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


def task_view(task: str):
    with div(Classes("flex flex-row justify-between items-center w-full")) as this:
        this >> span(Classes("text-lg")).text(task)
        this >> button(
            Classes("btn btn-error btn-square"), reactive=Reactive(delete(f"/delete?task={task}"), "closest div")
        ).append(icon("trash"))

    return this


def text_input():
    return input_(
        placeholder="What needs to be done?",
        name="task",
        classes=Classes("input input-primary w-96"),
        hsx="""
        on keyup[event.key == 'Escape']
            set my.value to ''
            my.blur()
        on keyup
            if my.value.length > 0
                remove .btn-disabled from #add-button
            else
                add .btn-disabled to #add-button
        """,
    )


def input_component():
    with form(
        Classes("flex flex-row justify-center items-center w-96 space-x-2"),
        reactive=Reactive(post("/add"), "#tasks", Swap.before_end),
        hsx="""
        on htmx:afterRequest
            my.reset()
            add .btn-disabled to #add-button
        """,
    ) as this:
        this >> text_input()
        this >> button(
            Classes("btn btn-primary btn-square btn-disabled"),
            element_id="add-button",
        ).append(icon("plus"))

    return this


def tasks_view():
    this = div(Classes("flex flex-col justify-center items-center w-96 space-y-2 mt-2"), element_id="tasks")
    for task in app.backend.state.tasks:
        this >> task_view(task)
    return this


def main_view():
    with div(Classes("flex flex-col justify-center items-center h-screen")) as mv:
        mv >> input_component()
        mv >> tasks_view()
    return mv


@app.backend.get("/")
def home():
    app.backend.state.tasks = ["task 1", "task 2", "task 3"]
    return app.doc.include(main_view()).to_response()


@app.backend.post("/add")
def add_task(task: Annotated[str, Form()]):
    logger.info(f"Adding task: {task}")
    app.backend.state.tasks.append(task)
    return task_view(task).to_response()


@app.backend.delete("/delete")
def delete_task(task: str):
    logger.info(f"Deleting task: {task}")
    app.backend.state.tasks.remove(task)
