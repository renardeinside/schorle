from lxml import etree
from pydantic import Field

from schorle.classes import Classes
from schorle.component import Component
from schorle.effector import effector
from schorle.element import button, div
from schorle.on import On
from schorle.page import Page
from schorle.reactives.state import ReactiveModel
from schorle.text import text
from schorle.utils import render_in_context


def test_reactive():
    class Sample(ReactiveModel):
        count: int = 0

        @effector
        def increment(self):
            self.count += 1

    class View(Component):
        counter: Sample

        def render(self):
            with button(on=On("click", self.counter.increment), classes=Classes("btn btn-primary")):
                text(f"Clicked {self.counter.count} times")

        def __init__(self, **data):
            super().__init__(**data)
            self.bind(self.counter)

    class ViewPage(Page):
        counter: Sample = Field(default_factory=Sample)

        def render(self):
            print("rendering with counter id", id(self.counter))
            with div(classes=Classes("flex justify-center items-center h-screen")):
                View(counter=self.counter).add()

    vp = ViewPage()

    r1 = render_in_context(vp)
    print("\n")
    print(etree.tostring(r1).decode())
    assert vp.counter.count == 0
    vp.counter.increment()
    assert vp.counter.count == 1
    r2 = render_in_context(vp)
    print("\n")
    print(etree.tostring(r2).decode())
