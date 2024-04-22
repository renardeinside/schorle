from typing import Callable

from fastapi.responses import HTMLResponse
from lxml import etree
from pydantic import Field

from schorle.component import Component
from schorle.element import body, div, head, link, meta, script, span, title
from schorle.rendering_context import rendering_context
from schorle.tags import HTMLTag
from schorle.text import text
from schorle.theme import Theme


class DevLoader(Component):
    def render(self):
        with div(classes="absolute bottom-4 right-4 hidden", element_id="dev_loader"):
            span(classes="loading loading-md loading-bars text-primary")


class Document(Component):
    page: Component
    title: str = "Schorle"
    theme: Theme = Theme.DARK
    with_dev_meta: bool = False
    extra_assets: Callable[..., None] | None = None
    lang: str = "en"
    with_tailwind: bool = True
    with_daisyui: bool = True
    with_dev_tools: bool = False
    daisyui_version: str = "4.7.2"
    body_attrs: dict[str, str] | None = Field(default_factory=dict)
    tag: HTMLTag = HTMLTag.HTML

    def __init__(self, **data):
        super().__init__(**data)
        self.element_id = None
        self.attrs = dict(lang=self.lang, **{"data-theme": self.theme})

    def render(self):
        with head():
            meta(charset="utf-8")
            meta(name="viewport", content="width=device-width, initial-scale=1.0")
            if self.with_dev_tools:
                meta(name="schorle-dev", content="true")
            with title():
                text(self.title)
            if self.with_dev_meta:
                meta(name="schorle-dev", content="true")

            link(href="/favicon.svg", rel="icon", type="image/svg+xml")
            if self.with_tailwind:
                script(src="https://cdn.tailwindcss.com")
            if self.with_daisyui:
                link(
                    href=f"https://cdn.jsdelivr.net/npm/daisyui@{self.daisyui_version}/dist/full.min.css",
                    rel="stylesheet",
                    type="text/css",
                )

            script(src="/_schorle/js/index.js", crossorigin="anonymous", defer="", **{"type": "module"})
            if self.extra_assets:
                self.extra_assets()

        with body(**self.body_attrs):
            self.page()

            if self.with_dev_tools:
                DevLoader()

    def to_response(self) -> HTMLResponse:
        with rendering_context(root=self) as rc:
            self.render()
        return HTMLResponse(
            etree.tostring(rc.to_lxml(), pretty_print=True).decode("utf-8"),
            200,
        )
