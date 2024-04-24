from contextlib import contextmanager

from schorle.component import Component
from schorle.element import div, h2, span
from schorle.rendering_context import rendering_context
from schorle.text import text


def test_c():
    class TestComponent(Component):
        def render(self):
            span()
            with div():
                div()
            with div():
                div()

    with rendering_context() as rc:
        TestComponent()

    assert len(rc.root._children) == 1


def test_subwrap():
    class TestComponent(Component):

        @staticmethod
        @contextmanager
        def card(title: str):
            with div(classes="card w-96 bg-base-100 shadow-xl"):
                with div(classes="card-body"):
                    with h2(classes="card-title"):
                        text(title)
                    yield

        def render(self):
            with self.card("card-1"):
                with div():
                    text("hey")
            with self.card("card-2"):
                with div():
                    text("ho")
