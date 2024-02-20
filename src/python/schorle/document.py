from typing import Any

from schorle.component import Component
from schorle.element import body, footer, head, link, meta, script, title
from schorle.page import Page
from schorle.tags import HTMLTag
from schorle.text import text
from schorle.theme import Theme


class Document(Component):
    tag: HTMLTag = HTMLTag.HTML
    title: str = "Schorle"
    theme: Theme = Theme.DARK
    page: Page | None = None
    with_dev_meta: bool = False
    extra_assets: list | None = None
    lang: str = "en"
    with_tailwind: bool = True
    with_daisyui: bool = True
    with_htmx: bool = True
    daisyui_version: str = "4.7.2"

    def model_post_init(self, __context: Any) -> None:
        self.attributes["lang"] = self.lang
        super().model_post_init(__context)

    def render(self):
        with head():
            meta(charset="utf-8")
            meta(name="viewport", content="width=device-width, initial-scale=1.0")
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

            script(src="/_schorle/assets/bundle.js", crossorigin="anonymous")
            if self.extra_assets:
                for asset in self.extra_assets:
                    asset()

            with title():
                text(self.title)
        with body():
            if self.page:
                with self.page:
                    self.page()

            if self.with_dev_meta:
                footer(element_id="schorle-footer")
