from schorle.component import Component
from schorle.document import Document
from schorle.theme import Theme


def test_empty_doc():
    _title = "Test Document"

    class PlaceholderPage(Component):
        element_id: str = "sample-component"

        def render(self):
            pass

    doc = Document(title=_title, page=PlaceholderPage(), theme=Theme.DARK)
    rendered = doc.to_string()
    assert rendered is not None
