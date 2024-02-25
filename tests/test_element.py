from lxml import etree

from schorle.attrs import Classes
from schorle.controller import RenderController
from schorle.element import div
from schorle.renderable import Renderable
from schorle.text import text


def test_el():
    class Fragment(Renderable):

        def render(self):
            with div():
                with div():
                    text("hey")

    with RenderController() as rc:
        root = rc.render(Fragment())
        assert etree.tostring(root).decode() == "<div><div>hey</div></div>"

    class AnotherFragment(Renderable):

        def render(self):
            with div():
                with div():
                    text("hey")
                with div():
                    text("ho")

    with RenderController() as rc:
        root = rc.render(AnotherFragment())
        assert etree.tostring(root).decode() == "<div><div>hey</div><div>ho</div></div>"


def test_with_attrs():
    class F(Renderable):
        def render(self):
            with div(element_id="level1"):
                with div(element_id="level2"):
                    text("hey")

    with RenderController() as rc:
        root = rc.render(F())
        assert etree.tostring(root).decode() == '<div id="level1"><div id="level2">hey</div></div>'

    class F2(Renderable):
        def render(self):
            with div(element_id="level1", classes=Classes("bg-red-500")):
                with div(element_id="level2"):
                    with div(element_id="level3"):
                        text("hey")

    with RenderController() as rc:
        root = rc.render(F2())
        assert (
            etree.tostring(root).decode()
            == '<div id="level1" class="bg-red-500"><div id="level2"><div id="level3">hey</div></div></div>'
        )
