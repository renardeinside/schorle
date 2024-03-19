from __future__ import annotations

from enum import Enum

from schorle.app import Schorle
from schorle.attrs import Classes
from schorle.controller import render
from schorle.element import button, div
from schorle.text import text
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


class Targets(str, Enum):
    counter = "counter"


def counter(count: int):
    with div(classes=Classes("flex flex-col justify-center items-center h-screen"), element_id=Targets.counter):
        with button(
            classes=Classes("btn btn-primary"), **{"hx-post": "/increment", "hx-target": f"#{Targets.counter}"}
        ):
            text(f"Count: {count}")


@app.backend.post("/increment")
def increment():
    app.backend.state.count += 1
    return render(counter, app.backend.state.count)


@app.backend.get("/")
def home():
    app.backend.state.count = 0
    return app.doc.render(counter, app.backend.state.count)
