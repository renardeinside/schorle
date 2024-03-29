from pydantic import BaseModel, Field

from schorle.attrs import Classes
from schorle.element import Element, div, html, span
from schorle.theme import Theme


class Document(BaseModel):
    title: str = "Schorle"
    theme: Theme = Theme.DARK
    with_dev_meta: bool = False
    extra_assets: list | None = None
    lang: str = "en"
    with_tailwind: bool = True
    with_daisyui: bool = True
    with_dev_tools: bool = False
    daisyui_version: str = "4.7.2"
    body_attributes: dict[str, str] | None = Field(default_factory=lambda: {"hx-ext": "morph, lucide"})

    def _base(self):
        with html(lang=self.lang, **{"data-theme": self.theme}) as _html:
            with _html.head() as _head:
                _head.meta(charset="utf-8")
                _head.meta(name="viewport", content="width=device-width, initial-scale=1.0")
                if self.with_dev_tools:
                    _head.meta(name="schorle-dev", content="true")
                _head.title().text(self.title)
                if self.with_dev_meta:
                    _head.meta(name="schorle-dev", content="true")

                _head.link(href="/favicon.svg", rel="icon", type="image/svg+xml")
                if self.with_tailwind:
                    _head.script(src="https://cdn.tailwindcss.com")
                if self.with_daisyui:
                    _head.link(
                        href=f"https://cdn.jsdelivr.net/npm/daisyui@{self.daisyui_version}/dist/full.min.css",
                        rel="stylesheet",
                        type="text/css",
                    )

                _head.script(src="https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js")
                _head.script(src="https://unpkg.com/idiomorph@0.3.0")
                _head.script(src="https://unpkg.com/idiomorph@0.3.0/dist/idiomorph-ext.min.js")
                _head.script(src="https://unpkg.com/hyperscript.org@0.9.12")
                _head.script(src="https://unpkg.com/lucide@latest")
                _head.script(src="/_schorle/assets/bundle.js", crossorigin="anonymous", defer="")
                if self.extra_assets:
                    for asset in self.extra_assets:
                        _head.append(asset)

            return _html

    def _dev_loader(self) -> Element:
        with div(Classes("absolute bottom-4 right-4 hidden"), element_id="dev_loader") as loader_container:
            loader_container >> span(Classes("loading loading-md loading-bars text-primary"))
        return loader_container

    def include(self, payload: Element) -> Element:
        _html = self._base()
        _body = _html.body(**self.body_attributes)
        _body.append(payload)
        if self.with_dev_tools:
            _body.append(self._dev_loader())
        return _html
