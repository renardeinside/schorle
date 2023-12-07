from typing import Callable, Optional

from lxml.etree import Element, tostring
from starlette.responses import HTMLResponse

from schorle.component import Component
from schorle.elements.base import BaseElement
from schorle.elements.html import body, head, html, link, meta, script, title
from schorle.page import Page
from schorle.theme import Theme


def _prepared_head():
    with head() as h:
        h.add(meta(charset="utf-8"))
        h.add(meta(name="viewport", content="width=device-width, initial-scale=1"))
        h.add(title("Schorle"))
        h.add(script(src="https://cdn.tailwindcss.com"))
        h.add(script(src="/_schorle/assets/bundle.js", crossorigin="anonymous"))
        h.add(
            link(href="https://cdn.jsdelivr.net/npm/daisyui@4.4.2/dist/full.min.css", rel="stylesheet", type="text/css")
        )
    return h


class Renderer:
    @classmethod
    async def render(cls, base_element: BaseElement, observer: Optional[Callable] = None) -> Element:
        _cleansed_attrs = {k: v for k, v in base_element.attrs.items() if v is not None}
        element = Element(base_element.tag, **_cleansed_attrs)
        for child in base_element.children:
            if isinstance(child, BaseElement):
                if observer:
                    child.subscribe(observer)

                _r = await cls.render(child, observer)

                element.append(_r)
            elif isinstance(child, Component):
                _pre_rendered = await child.render()
                _r = await cls.render(_pre_rendered, observer)
                element.append(_r)

            else:
                element.text = str(child)
        return element

    @classmethod
    async def render_to_response(cls, page: Page, theme: Theme, observer: Optional[Callable] = None) -> HTMLResponse:
        _head = _prepared_head()
        _html = html(_head, body(page), **{"data-theme": theme})

        rendered = await cls.render(_html, observer)

        _prepared = tostring(
            rendered,
            pretty_print=True,
            doctype="<!DOCTYPE html>",
        ).decode("utf-8")

        return HTMLResponse(
            _prepared,
            status_code=200,
        )
