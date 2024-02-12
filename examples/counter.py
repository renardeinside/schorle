from __future__ import annotations

from schorle.app import Schorle
from schorle.classes import Classes
from schorle.element import button, div
from schorle.on import On
from schorle.page import Page
from schorle.text import text

app = Schorle()


class PageWithButton(Page):
    def render(self):
        with div(classes=Classes("flex justify-center items-center h-screen")):
            with button(
                classes=Classes("btn btn-success"),
                on=On("click", lambda: print("Button clicked!")),
            ):
                text("Click me!")


@app.get("/")
def get_page():
    return PageWithButton()
