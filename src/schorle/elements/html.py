from uuid import uuid4

from pydantic import Field

from schorle.attribute import Attribute
from schorle.elements.base.base import BaseElement
from schorle.elements.base.element import Element
from schorle.elements.page import Page
from schorle.elements.tags import HTMLTag
from schorle.theme import Theme


class Meta(BaseElement):
    tag: HTMLTag = HTMLTag.META
    charset: str = Attribute(default=None)
    name: str = Attribute(default=None)
    content: str = Attribute(default=None)


class Title(BaseElement):
    tag: HTMLTag = HTMLTag.TITLE
    text: str = "Schorle"


class HeadLink(BaseElement):
    tag: HTMLTag = HTMLTag.LINK
    href: str = Attribute(default=None)
    rel: str = Attribute(default=None)
    type_: str | None = Attribute(default=None, alias="type")


class Script(BaseElement):
    tag: HTMLTag = HTMLTag.SCRIPT
    src: str = Attribute(default=None)
    crossorigin: str = Attribute(default=None)
    text: str = ""  # we always want to have a closing tag
    defer: str | None = Attribute(default=None)


class CSRFMeta(Meta):
    tag: HTMLTag = HTMLTag.META
    name: str = Attribute(default="schorle-csrf-token")
    content: str = Attribute(default_factory=lambda: str(uuid4()))


class ExtraAssets(BaseElement):
    render_behaviour: str = "flatten"
    tag: HTMLTag = HTMLTag.DIV
    elements: list[BaseElement] = Field(default_factory=list)


class Head(BaseElement):
    tag: HTMLTag = HTMLTag.HEAD
    charset_meta: Meta = Meta(charset="utf-8")
    viewport_meta: Meta = Meta(name="viewport", content="width=device-width, initial-scale=1.0")
    csrf_meta: CSRFMeta = CSRFMeta()
    dev_meta: Meta | None = None
    title: Title = Title()
    favicon: HeadLink = HeadLink(href="/favicon.svg", rel="icon", type_="image/svg+xml")
    # css-related
    daisy_ui: HeadLink = HeadLink(
        href="https://cdn.jsdelivr.net/npm/daisyui@4.6.1/dist/full.min.css", rel="stylesheet", type_="text/css"
    )
    tailwind: Script = Script(src="https://cdn.tailwindcss.com")
    # htmx
    htmx: Script = Script(src="https://unpkg.com/htmx.org@1.9.10", crossorigin="anonymous")
    htmx_ws: Script = Script(src="https://unpkg.com/htmx.org@1.9.10/dist/ext/ws.js")
    idiomorph: Script = Script(src="https://unpkg.com/idiomorph@0.3.0")
    # todo: use idiomorph-htmx when bug is fixed
    # idiomorph_htmx: Script.provide(src="https://unpkg.com/idiomorph/dist/idiomorph-ext.min.js")
    # client-side bundle
    bundle: Script = Script(src="/_schorle/assets/bundle.js", crossorigin="anonymous")
    extra_assets: ExtraAssets = ExtraAssets.factory()


class Footer(BaseElement):
    tag: HTMLTag = HTMLTag.FOOTER
    text: str = ""


class DevFooter(BaseElement):
    tag: HTMLTag = HTMLTag.FOOTER
    text: str = ""


class Body(BaseElement):
    tag: HTMLTag = HTMLTag.BODY
    footer: DevFooter = DevFooter(element_id="schorle-footer")


class Html(BaseElement):
    tag: HTMLTag = HTMLTag.HTML
    theme: Theme = Attribute(..., alias="data-theme")
    head: Head = Field(default_factory=Head)
    body: Body = Field(default_factory=Body)


class Div(Element):
    tag: HTMLTag = HTMLTag.DIV


class EventHandler(BaseElement):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-event-handler"
    hx_ws: str = Attribute(default="ws,event-header", alias="hx-ext")
    ws_connect: str = Attribute(default="/_schorle/events", alias="ws-connect")
    content: Page


class MorphWrapper(BaseElement):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-morph-wrapper"
    morph: str = Attribute(default="morph", alias="hx-ext")
    handler: EventHandler


class BodyWithPage(Body):
    wrapper: MorphWrapper


class Paragraph(Element):
    tag: HTMLTag = HTMLTag.P


class Span(Element):
    tag: HTMLTag = HTMLTag.SPAN
