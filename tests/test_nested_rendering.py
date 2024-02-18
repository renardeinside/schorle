from loguru import logger
from lxml import etree

from schorle.classes import Classes
from schorle.component import Component
from schorle.element import button, div, span
from schorle.page import Page
from schorle.text import text
from schorle.utils import render_in_context


class C(Component):
    def render(self):
        with button():
            with span(classes=Classes("htmx-indicator")):
                with span(classes=Classes("loading loading-infinity")):
                    pass

            with span():
                text("something")


class P(Page):
    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            C()


def test_nested():
    page = P()
    rendered = render_in_context(page, page=page)
    logger.debug(etree.tostring(rendered, pretty_print=True).decode())
