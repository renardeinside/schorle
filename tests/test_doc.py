from lxml import etree
from pydantic import Field

from schorle.component import Component
from schorle.document import Document
from schorle.element import button, div, span
from schorle.page import Page
from schorle.text import text


def test_doc():
    class SamplePage(Page):
        def render(self):
            with div():
                text("Hello, World!")

    doc = Document(title="Test Document", page=SamplePage())

    print(etree.tostring(doc.render(), pretty_print=True).decode("utf-8"))


def test_components():
    class SampleComponent(Component):
        def render(self):
            with div():
                with span():
                    text("Hello from component!")
                with button():
                    text("Click me!")

    class SamplePage(Page):
        components: list[Component] = Field(default_factory=list)

        def render(self):
            for component in self.components:
                component()

    page = SamplePage(components=[SampleComponent() for _ in range(3)])
    doc = Document(title="Test Document", page=page)
    print(etree.tostring(doc.render(), pretty_print=True).decode("utf-8"))
