from functools import partial
from typing import Any, Callable

from pydantic import BaseModel, Field

from schorle.controller import render
from schorle.element import body, head, html, link, meta, script, title
from schorle.text import text
from schorle.theme import Theme


class Document(BaseModel):
    title: str = "Schorle"
    theme: Theme = Theme.DARK
    with_dev_meta: bool = False
    extra_assets: list | None = None
    lang: str = "en"
    with_tailwind: bool = True
    with_daisyui: bool = True
    daisyui_version: str = "4.7.2"
    body_attributes: dict[str, str] | None = Field(default_factory=lambda: {"hx-ext": "morph, lucide"})

    def _render(self, payload: Callable[..., Any] | None = None):
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
                script(src="https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js")
                script(src="https://unpkg.com/idiomorph@0.3.0")
                script(src="https://unpkg.com/idiomorph@0.3.0/dist/idiomorph-ext.min.js")
                script(src="https://unpkg.com/hyperscript.org@0.9.12")
                script(src="/_schorle/assets/bundle.js", crossorigin="anonymous", **{"defer": ""})
                if self.extra_assets:
                    for asset in self.extra_assets:
                        asset()

                with title():
                    text(self.title)
            with body(attrs=self.body_attributes):
                if payload:
                    payload()

    def render(self, payload: Callable[..., Any] | None = None, *args, **kwargs):
        return render(partial(self._render, partial(payload, *args, **kwargs)))
