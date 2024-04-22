from schorle.component import Component
from schorle.element import div, span
from schorle.rendering_context import rendering_context


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
