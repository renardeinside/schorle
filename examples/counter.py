from __future__ import annotations

from schorle.app import Schorle
from schorle.attrs import Classes
from schorle.button import Button
from schorle.component import Component
from schorle.element import div
from schorle.page import Page
from schorle.text import text
from schorle.theme import Theme

app = Schorle(theme=Theme.AUTUMN)


class StatefulButton(Component):

    def render(self):
        with Button(modifier="primary"):
            text("Click me")


class PageWithButton(Page):

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            StatefulButton()


@app.get("/")
def get_page():
    return PageWithButton()
