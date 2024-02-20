from schorle.classes import Classes
from schorle.component import Component
from schorle.element import span
from schorle.text import text


class Loading(Component):
    lazy_append: bool = True
    classes: Classes = Classes("flex justify-center items-center w-full h-full")

    def render(self):
        with span(classes=Classes("loading loading-md loading-bars")):
            text("")
