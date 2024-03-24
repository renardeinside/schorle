import textwrap

from lxml import etree

from schorle.document import Document


def test_empty_doc():
    _title = "Test Document"
    doc = Document(title=_title)
    lnk = f"https://cdn.jsdelivr.net/npm/daisyui@{doc.daisyui_version}/dist/full.min.css"
    result = etree.tostring(doc._base()._compose(doc._base()), pretty_print=True).decode()
    expected = textwrap.dedent(
        f"""\
        <html lang="en" data-theme="dark">
          <head>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
            <title>Test Document</title>
            <link href="/favicon.svg" rel="icon" type="image/svg+xml"></link>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://cdn.jsdelivr.net/npm/daisyui@4.7.2/dist/full.min.css" rel="stylesheet" type="text/css"></link>
            <script src="https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js"></script>
            <script src="https://unpkg.com/idiomorph@0.3.0"></script>
            <script src="https://unpkg.com/idiomorph@0.3.0/dist/idiomorph-ext.min.js"></script>
            <script src="https://unpkg.com/hyperscript.org@0.9.12"></script>
            <script src="https://unpkg.com/lucide@latest"></script>
            <script src="/_schorle/assets/bundle.js" crossorigin="anonymous" defer=""></script>
          </head>
        </html>
    """
    )
    print(result)
    assert result == expected
