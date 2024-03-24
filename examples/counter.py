from __future__ import annotations

from schorle.app import Schorle
from schorle.attrs import Classes
from schorle.element import button, div
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


def counter():
    return button(
        Classes("btn btn-primary"),
        hsx="""
            init
                set my.count to 0
            on click
                set my.count to my.count + 1
                put `Clicked ${my.count} times!` into me
            """,
    ).text("Click me!")


@app.backend.get("/")
def home():
    mv = div(classes=Classes("flex flex-col justify-center items-center h-screen")).append(counter())
    return app.doc.include(mv).to_response()
