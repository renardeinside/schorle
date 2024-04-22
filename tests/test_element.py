from lxml import etree

from schorle.element import div, span
from schorle.rendering_context import rendering_context


def test_one():
    with rendering_context() as rc:
        div()

    assert len(rc.root._children) == 1


def test_multi_exit():
    with rendering_context() as rc:
        with div():
            with div():
                div()
            with span():
                div()
        div()

    rendered = etree.tostring(rc.to_lxml(), pretty_print=False).decode("utf-8")
    assert rendered == "<root><div><div><div></div></div><span><div></div></span></div><div></div></root>"
