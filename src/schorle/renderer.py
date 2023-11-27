from lxml.etree import Element, tostring
from starlette.responses import HTMLResponse

from schorle.elements.base import BaseElement
from schorle.elements.html import body, head, html, link, meta, script, title
from schorle.page import Page
from schorle.signal import Signal
from schorle.theme import Theme


def _prepared_head():
    return head(
        meta(charset="utf-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1"),
        title("Schorle"),
        script(src="https://cdn.tailwindcss.com"),
        script(src="/_schorle/assets/bundle.js", crossorigin="anonymous"),
        link(href="https://cdn.jsdelivr.net/npm/daisyui@4.4.2/dist/full.min.css", rel="stylesheet", type="text/css"),
    )


class Renderer:
    @classmethod
    def _render(cls, base_element: BaseElement) -> Element:
        element = Element(base_element.tag, **base_element.attrs)
        for child in base_element.children:
            if isinstance(child, BaseElement):
                element.append(cls._render(child))
            elif isinstance(child, Signal):
                element.text = str(child.value)
            else:
                element.text = str(child)
        return element

    @classmethod
    def render(cls, base_element: BaseElement) -> str:
        return tostring(cls._render(base_element), pretty_print=True).decode("utf-8")

    @classmethod
    def render_to_response(cls, page: Page, theme: Theme) -> HTMLResponse:
        _prepared = tostring(
            Renderer._render(html(_prepared_head(), body(page), **{"data-theme": theme})),
            pretty_print=True,
            doctype="<!DOCTYPE html>",
        ).decode("utf-8")

        return HTMLResponse(
            _prepared,
            status_code=200,
        )
