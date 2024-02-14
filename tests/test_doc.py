from lxml import etree

from schorle.document import Document
from schorle.element import div
from schorle.page import Page
from schorle.text import text
from schorle.utils import render_in_context


def test_doc():
    class SamplePage(Page):
        def render(self):
            with div():
                text("Hello, World!")

    doc = Document(title="Test Document", page=SamplePage())
    root = render_in_context(doc)
    print(etree.tostring(root, pretty_print=True).decode())
