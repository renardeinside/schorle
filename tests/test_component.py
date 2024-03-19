from lxml import etree

from schorle.component import Component
from schorle.controller import RenderController
from schorle.element import div
from schorle.text import text


def test_component_empty():
    class C(Component):
        def render(self):
            pass

    with RenderController() as rc:
        _lxml = rc.render(C())
        assert etree.tostring(_lxml) == b"<schorle-component/>"


def test_component_with_text():
    class C(Component):
        def render(self):
            text("Hello, World!")

    with RenderController() as rc:
        _lxml = rc.render(C())
        assert etree.tostring(_lxml) == b"<schorle-component>Hello, World!</schorle-component>"


def test_component_with_div():
    class C(Component):
        def render(self):
            with div():
                text("Hello, World!")

    with RenderController() as rc:
        _lxml = rc.render(C())
        assert etree.tostring(_lxml) == b"<schorle-component><div>Hello, World!</div></schorle-component>"


def test_nested_components():
    class C1(Component):
        def render(self):
            text("Hello, World!")

    class C(Component):

        def render(self):
            C1()

    with RenderController() as rc:
        _lxml = rc.render(C())
        assert (
            etree.tostring(_lxml)
            == b"<schorle-component><schorle-component>Hello, World!</schorle-component></schorle-component>"
        )
