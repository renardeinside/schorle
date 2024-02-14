from lxml import etree

from schorle.component import Component
from schorle.element import button, div
from schorle.page import Page
from schorle.tags import HTMLTag
from schorle.text import text
from schorle.utils import render_in_context


class Button(Component):
    tag: HTMLTag = HTMLTag.BUTTON

    def render(self):
        text("Hey!")


class SamplePage(Page):
    def render(self):
        with div():
            with button():
                text("Hello, World!")


def test_context_rendering():
    print("\n\n\n")
    page = SamplePage()
    rendered = render_in_context(page)
    print(etree.tostring(rendered, pretty_print=True).decode())
