from lxml import etree

from schorle.classes import Classes
from schorle.component import Component
from schorle.document import Document
from schorle.element import button, div
from schorle.page import Page
from schorle.text import text
from schorle.utils import render_in_context


def test_doc():
    class C1(Component):
        def render(self):
            with div(classes=Classes("flex justify-center items-center h-screen")):
                text("Hello")

    class SamplePage(Page):
        def render(self):
            with button(classes=Classes("btn btn-primary")):
                text("Increment")
            with button(classes=Classes("btn btn-secondary")):
                text("Decrement")
            C1()

    doc = Document(title="Test Document", page=SamplePage())
    root = render_in_context(doc)
    print(etree.tostring(root, pretty_print=True).decode())
