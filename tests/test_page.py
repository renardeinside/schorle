from lxml import etree

from schorle.controller import RenderController
from schorle.element import div
from schorle.page import Page
from schorle.text import text


def test_with_page():

    class SamplePage(Page):
        def render(self):
            with div():
                text("Hello, World!")

    with RenderController() as rc:
        _lxml = rc.render(SamplePage())
        assert etree.tostring(_lxml) == b"<schorle-page><div>Hello, World!</div></schorle-page>"
