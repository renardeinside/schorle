import textwrap

from loguru import logger
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
                <meta charset="utf-8"></meta>
                <meta name="viewport" content="width=device-width, initial-scale=1.0"></meta>
                <link href="/favicon.svg" rel="icon" type="image/svg+xml"></link>
                <script src="https://cdn.tailwindcss.com"></script>
                <link href="{lnk}" rel="stylesheet" type="text/css"></link>
                <script src="/_schorle/assets/bundle.js" crossorigin="anonymous" defer=""></script>
                <title>Test Document</title>
              </head>
              <body></body>
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
    doc = Document(title="with page", page=page)
    with RenderController() as rc:
        _lxml = rc.render(doc)
        logger.debug(etree.tostring(_lxml, pretty_print=True).decode())
        # # find element with div and id schorle-page
        page = _lxml.xpath("//div[@id='schorle-page']")[0]
        # # check that page has a child div with text "Hello, World!"
        assert page.xpath(".//div[text()='Hello, World!']")
        # # check that all page children have id
        for child in page.getchildren():
            assert "id" in child.attrib
