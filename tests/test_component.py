from lxml import etree

from schorle.attrs import Classes
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
        assert etree.tostring(_lxml) == b"<div/>"


def test_component_with_text():
    class C(Component):
        def render(self):
            text("Hello, World!")

    with RenderController() as rc:
        _lxml = rc.render(C())
        assert etree.tostring(_lxml) == b"<div>Hello, World!</div>"


def test_component_with_div():
    class C(Component):
        def render(self):
            with div():
                text("Hello, World!")

    with RenderController() as rc:
        _lxml = rc.render(C())
        assert etree.tostring(_lxml) == b"<div><div>Hello, World!</div></div>"


def test_nested_components():
    class C1(Component):
        element_id: str = "child"

        def render(self):
            text("Hello, World!")

    class C(Component):
        element_id: str = "parent"

        def render(self):
            C1()

    with RenderController() as rc:
        _lxml = rc.render(C())
        assert etree.tostring(_lxml) == b'<div id="parent"><div id="child">Hello, World!</div></div>'


def test_component_with_classes():
    class C(Component):
        classes: Classes = Classes("class1 class2")

        def render(self):
            text("Hello, World!")

    with RenderController() as rc:
        _lxml = rc.render(C())
        assert etree.tostring(_lxml) == b'<div class="class1 class2">Hello, World!</div>'
