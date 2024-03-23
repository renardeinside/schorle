from __future__ import annotations

from schorle.app import Schorle
from schorle.attrs import Classes
from schorle.element import div
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


def main_view():
    with div(Classes("flex flex-col items-center justify-center h-screen")) as mv:
        mv.button(
            Classes("btn btn-primary"),
            hsx="""
            init
                set my.count to 0
            on click
                set my.count to my.count + 1
                put `Clicked ${my.count} times!` into me
            """,
        ).text("Click me!")
    return mv


@app.backend.get("/")
def home():
    return app.doc.include(main_view()).to_response()
