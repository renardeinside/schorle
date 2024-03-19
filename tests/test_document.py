import textwrap

from lxml import etree

from schorle.controller import RenderController
from schorle.document import Document
from schorle.element import div
from schorle.page import Page
from schorle.text import text


def test_empty_doc():
    _title = "Test Document"
    doc = Document(title=_title)
    lnk = f"https://cdn.jsdelivr.net/npm/daisyui@{doc.daisyui_version}/dist/full.min.css"
    with RenderController() as rc:
        root = rc.render(doc)
        result = etree.tostring(root, pretty_print=True).decode()
        expected = textwrap.dedent(
            f"""\
            <html lang="en" theme="dark" data-theme="dark">
              <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <link href="/favicon.svg" rel="icon" type="image/svg+xml"></link>
                <script src="https://cdn.tailwindcss.com"></script>
                <link href="{lnk}" rel="stylesheet" type="text/css"></link>
                <script src="https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js"></script>
                <script src="https://unpkg.com/idiomorph@0.3.0"></script>
                <script src="https://unpkg.com/idiomorph@0.3.0/dist/idiomorph-ext.min.js"></script>
                <title>Test Document</title>
              </head>
              <body/>
            </html>
        """
        )
        assert result == expected


def test_with_page():
    class SamplePage(Page):
        def render(self):
            with div():
                text("Hello, World!")

    _title = "with page"
    page = SamplePage()
    doc = Document(title="with page", page=page, with_daisyui=False, with_tailwind=False)
    with RenderController() as rc:
        _lxml = rc.render(doc)
        _rendered = etree.tostring(_lxml, pretty_print=True).decode()
        expected = textwrap.dedent(
            f"""\
            <html lang="en" theme="dark" data-theme="dark">
              <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
                <link href="/favicon.svg" rel="icon" type="image/svg+xml"></link>
                <script src="https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js"></script>
                <script src="https://unpkg.com/idiomorph@0.3.0"></script>
                <script src="https://unpkg.com/idiomorph@0.3.0/dist/idiomorph-ext.min.js"></script>
                <title>{_title}</title>
              </head>
              <body>
                <schorle-page>
                  <div>Hello, World!</div>
                </schorle-page>
              </body>
            </html>
        """
        )
        assert _rendered == expected
