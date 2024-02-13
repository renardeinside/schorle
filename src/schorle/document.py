from uuid import UUID, uuid4

from pydantic import Field

from schorle.attribute import Attribute, Id
from schorle.component import Component
from schorle.element import body, div, footer, head, html, link, meta, script, title
from schorle.page import Page
from schorle.text import text
from schorle.theme import Theme


class Document(Component):
    title: str = "Schorle"
    csrf_token: UUID = Field(default_factory=uuid4)
    theme: Theme = Theme.DARK
    page: Page | None = None
    with_dev_meta: bool = False
    extra_assets: list | None = None
    lang: str = "en"

    def render(self):
        with html(theme=Attribute(alias="data-theme", value=self.theme.value), lang=self.lang):
            with head():
                meta(charset="utf-8")
                meta(name="viewport", content="width=device-width, initial-scale=1.0")
                meta(name="schorle-csrf-token", content=str(self.csrf_token))
                if self.with_dev_meta:
                    meta(name="schorle-dev", content="true")
                link(href="/favicon.svg", rel="icon", type="image/svg+xml")
                script(src="https://cdn.tailwindcss.com")
                script(src="https://unpkg.com/htmx.org@1.9.10", crossorigin="anonymous")
                script(src="https://unpkg.com/htmx.org@1.9.10/dist/ext/ws.js")
                script(src="https://unpkg.com/idiomorph@0.3.0")
                link(
                    href="https://cdn.jsdelivr.net/npm/daisyui@4.7.0/dist/full.min.css",
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
                with div(_id=Id("schorle-morph-wrapper"), ext=Attribute(alias="hx-ext", value="morph")):
                    with div(
                        _id=Id("schorle-event-handler"),
                        ext=Attribute(alias="hx-ext", value="ws,event-header"),
                        ws_connect=Attribute(alias="ws-connect", value="/_schorle/events"),
                    ):
                        if self.page:
                            with self.page:
                                self.page()
                if self.with_dev_meta:
                    footer(_id=Id("schorle-footer"))
