from schorle.classes import Classes
from schorle.component import Component
from schorle.element import span
from schorle.text import text


class Loading(Component):
    def render(self):
        with span(classes=Classes("loading loading-md loading-spinner")):
            text("")
