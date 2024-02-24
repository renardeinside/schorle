from pydantic import BaseModel

from schorle._dev import dev_loading_spinner
from schorle.element import body, footer, head, html, link, meta, script, title
from schorle.page import Page
from schorle.renderable import Renderable
from schorle.text import text
from schorle.theme import Theme


class Document(Renderable, BaseModel):
    title: str = "Schorle"
    theme: Theme = Theme.DARK
    with_dev_meta: bool = False
    extra_assets: list | None = None
    lang: str = "en"
    with_tailwind: bool = True
    with_daisyui: bool = True
    daisyui_version: str = "4.7.2"
    page: Page | None = None

    def render(self):
        with html(lang=self.lang, theme=self.theme, **{"data-theme": self.theme}):
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

                script(src="/_schorle/assets/bundle.js", crossorigin="anonymous", **{"defer": ""})
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
                    with footer(element_id="schorle-footer"):
                        dev_loading_spinner()
