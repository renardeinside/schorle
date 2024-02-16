from pydantic import Field

from schorle.classes import Classes
from schorle.component import Component
from schorle.effector import effector
from schorle.element import button, div, span
from schorle.page import Page
from schorle.state import ReactiveModel
from schorle.text import text
from schorle.types import LXMLElement
from schorle.utils import render_in_context


def test_reactive():
    class Sample(ReactiveModel):
        count: int = 0

        @effector
        def increment(self):
            self.count += 1

    class Another(Component):
        def render(self):
            with span():
                text("Something")

    class View(Component):
        counter: Sample

        def render(self):
            with button(classes=Classes("btn btn-primary")):
                text(f"Clicked {self.counter.count} times")
            Another()

        def __init__(self, **data):
            super().__init__(**data)
            self.bind(self.counter)

    class ViewPage(Page):
        counter: Sample = Field(default_factory=Sample)

        def render(self):
            with div(classes=Classes("flex justify-center items-center h-screen")):
                View(counter=self.counter, element_id="v1")
            View(counter=self.counter)

    vp = ViewPage()

    with vp:
        r1 = render_in_context(vp)
        assert isinstance(r1, LXMLElement)
