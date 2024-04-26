import textwrap

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
    expected = textwrap.dedent(
        f"""\
        <html data-theme="dark" lang="en">
          <head>
            <meta charset="utf-8"></meta>
            <meta name="viewport" content="width=device-width, initial-scale=1.0"></meta>
            <title>{_title}</title>
            <link href="/favicon.svg" rel="icon" type="image/svg+xml"></link>
            <script src="/_schorle/dist/tailwind.min.js.br"></script>
            <link href="/_schorle/dist/daisyui.min.css.br" rel="stylesheet"></link>
            <script src="/_schorle/js/index.min.js.br" crossorigin="anonymous" defer="" type="module"></script>
          </head>
          <body>
            <div id="schorle-page">
              <div id="sample-component"></div>
            </div>
          </body>
        </html>
    """
    )
    assert rendered == expected
