from lxml import etree

from schorle.classes import Classes
from schorle.document import Document
from schorle.element import button, div
from schorle.page import Page
from schorle.text import text
from schorle.utils import render_in_context


def test_doc():
    class SamplePage(Page):
        def render(self):
            with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
                with div(classes=Classes("flex flex-row justify-center items-center")):
                    with button(classes=Classes("btn btn-primary")):
                        text("Increment")
                    with button(classes=Classes("btn btn-secondary")):
                        text("Decrement")
                with div(classes=Classes("text-2xl")):
                    text("Counter something")

    doc = Document(title="Test Document", page=SamplePage())
    root = render_in_context(doc)
    result = etree.tostring(root, pretty_print=True).decode()
    assert isinstance(result, str)
