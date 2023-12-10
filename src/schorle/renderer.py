from typing import Callable, Optional

from loguru import logger
from lxml.etree import Element as LxmlElement
from lxml.etree import tostring
from starlette.responses import HTMLResponse

from schorle.elements.base import Element
from schorle.elements.html import body, head, html, link, meta, script, title
from schorle.page import Page
from schorle.theme import Theme


def _prepared_head():
    h = head()
    with h.layout:
        meta(charset="utf-8").add()
        meta(name="viewport", content="width=device-width, initial-scale=1").add()
        title("Schorle").add()
        script(src="https://cdn.tailwindcss.com").add()
        script(src="/_schorle/assets/bundle.js", crossorigin="anonymous").add()
        link(
            href="https://cdn.jsdelivr.net/npm/daisyui@4.4.2/dist/full.min.css", rel="stylesheet", type="text/css"
        ).add()
    return h


class Renderer:
    @classmethod
    def render(cls, base_element: Element, observer: Optional[Callable] = None) -> LxmlElement:
        logger.debug(f"Rendering {base_element}")
        _cleansed_attrs = {k: v for k, v in base_element.attrs.items() if v is not None}
        element = LxmlElement(base_element.tag, **_cleansed_attrs)
        for child in base_element.children:
            if isinstance(child, Element):
                _r = cls.render(child, observer)
                element.append(_r)
            else:
                element.text = str(child)
        return element

    @classmethod
    def render_to_response(cls, page: Page, theme: Theme, observer: Optional[Callable] = None) -> HTMLResponse:
        _head = _prepared_head()
        _html = html(_head, body(page), **{"data-theme": theme.value})

        rendered = cls.render(_html, observer)

        _prepared = tostring(
            rendered,
            pretty_print=True,
            doctype="<!DOCTYPE html>",
        ).decode("utf-8")

        return HTMLResponse(
            _prepared,
            status_code=200,
        )
