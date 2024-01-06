from uuid import uuid4

from pydantic import Field

from schorle.elements.base import Element, ElementWithGeneratedId
from schorle.elements.page import Page
from schorle.elements.tags import HTMLTag
from schorle.theme import Theme


def Attribute(*args, **kwargs):  # noqa: N802
    """
    This is a helper function to make it easier to annotate attributes on elements.
    :param args: same as pydantic.Field
    :param kwargs: same as pydantic.Field
    """
    kwargs["attribute"] = True
    return Field(*args, **kwargs)


class Meta(Element):
    tag: HTMLTag = HTMLTag.META
    charset: str = Attribute(default=None)
    name: str = Attribute(default=None)
    content: str = Attribute(default=None)


class Title(Element):
    tag: HTMLTag = HTMLTag.TITLE
    text: str = "Schorle"


class Link(Element):
    tag: HTMLTag = HTMLTag.LINK
    href: str = Attribute(default=None)
    rel: str = Attribute(default=None)
    type_: str = Attribute(default=None, alias="type")


class Script(Element):
    tag: HTMLTag = HTMLTag.SCRIPT
    src: str = Attribute(default=None)
    crossorigin: str = Attribute(default=None)
    text: str = ""  # we always want to have a closing tag
    defer: str | None = Attribute(default=None)


class CSRFMeta(Meta):
    tag: HTMLTag = HTMLTag.META
    name: str = Attribute(default="schorle-csrf-token")
    content: str = Attribute(default_factory=lambda: str(uuid4()))


class Head(Element):
    tag: HTMLTag = HTMLTag.HEAD
    charset_meta: Meta.provide(charset="utf-8")
    viewport_meta: Meta.provide(name="viewport", content="width=device-width, initial-scale=1")
    csrf_meta: CSRFMeta.provide()
    title: Title.provide()
    daisy_ui: Link.provide(
        href="https://cdn.jsdelivr.net/npm/daisyui@4.4.22/dist/full.min.css", rel="stylesheet", type="text/css"
    )
    tailwind: Script.provide(src="https://cdn.tailwindcss.com")
    htmx: Script.provide(src="/_schorle/assets/htmx.js", crossorigin="anonymous")
    htmx_ws: Script.provide(src="_schorle/assets/ws.js", crossorigin="anonymous")
    idiomorph: Script.provide(src="/_schorle/assets/idiomorph.js", crossorigin="anonymous")
    idiomorph_htmx: Script.provide(src="/_schorle/assets/idiomorph-htmx.js", crossorigin="anonymous")
    bundle: Script.provide(src="/_schorle/assets/bundle.js", crossorigin="anonymous")


class Body(Element):
    tag: HTMLTag = HTMLTag.BODY


class Html(Element):
    tag: HTMLTag = HTMLTag.HTML
    theme: Theme = Attribute(..., alias="data-theme")
    head: Head.provide()
    body: Body.provide()


class Div(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.DIV


class EventHandler(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-event-handler"
    hx_ws: str = Attribute(default="ws", alias="hx-ext")
    ws_connect: str = Attribute(default="/_schorle/events", alias="ws-connect")
    content: Page


class MorphWrapper(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-morph-wrapper"
    morph: str = Attribute(default="morph", alias="hx-ext")
    handler: EventHandler.provide()


class BodyWithPage(Body):
    wrapper: MorphWrapper.provide()


class Paragraph(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.P


class Span(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.SPAN
