from typing import Optional, Union

from pydantic import Field
from starlette.responses import HTMLResponse

from schorle.elements.base import Element, ElementWithGeneratedId, Subscriber
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
    text: str = ""
    defer: str | None = Attribute(default=None)


class Head(Element):
    tag: HTMLTag = HTMLTag.HEAD
    charset_meta: Meta.provide(charset="utf-8")
    viewport_meta: Meta.provide(name="viewport", content="width=device-width, initial-scale=1")
    title: Title.provide()
    daisy_ui: Link.provide(
        href="https://cdn.jsdelivr.net/npm/daisyui@4.4.22/dist/full.min.css", rel="stylesheet", type="text/css"
    )
    tailwind: Script.provide(src="https://cdn.tailwindcss.com")
    htmx: Script.provide(src="/_schorle/assets/htmx.js", crossorigin="anonymous")
    htmx_ws: Script.provide(src="https://unpkg.com/htmx.org/dist/ext/ws.js", crossorigin="anonymous")
    idiomorph: Script.provide(src="/_schorle/assets/idiomorph.js", crossorigin="anonymous")
    idiomorph_htmx: Script.provide(src="/_schorle/assets/idiomorph-htmx.js", crossorigin="anonymous")
    bundle: Script.provide(src="/_schorle/assets/bundle.js", crossorigin="anonymous")


class Body(Element):
    tag: HTMLTag = HTMLTag.BODY


class Html(Element):
    tag: HTMLTag = HTMLTag.HTML
    theme: Theme = Attribute(default=Theme.DARK, alias="data-theme")
    head: Head.provide()
    body: Body.provide()


class Div(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.DIV


class Span(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.SPAN


class EventHandler(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-event-handler"
    hx_ws: str = Attribute(default="ws", alias="hx-ext")
    ws_connect: str = Attribute(default="/_schorle/events", alias="ws-connect")
    content: "Page"


class MorphWrapper(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-morph-wrapper"
    morph: str = Attribute(default="morph", alias="hx-ext")
    handler: EventHandler.provide()


class BodyWithPage(Body):
    wrapper: MorphWrapper.provide()


class DeveloperTools(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-developer-tools"
    hx_ws: str = Attribute(default="ws", alias="hx-ext")
    ws_connect: str = Attribute(default="/_schorle/devtools", alias="ws-connect")


class BodyWithPageAndDeveloperTools(BodyWithPage):
    developer_tools: DeveloperTools.provide()


BodyClasses = Union[type[Body], type[BodyWithPage], type[BodyWithPageAndDeveloperTools]]


class Page(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    def render_to_response(self, body_class: Optional[BodyClasses] = BodyWithPage) -> HTMLResponse:
        handler = EventHandler(content=self)
        body = body_class(wrapper=MorphWrapper(handler=handler))
        html = Html(body=body)
        response = HTMLResponse(html.render(), status_code=200)
        return response

    def find_by_id(self, element_id: str) -> Optional[Element]:
        for child in self._traverse_elements(nested=True):
            if child.element_id == element_id:
                return child
        return None

    def set_subscriber(self, subscriber: Subscriber):
        self._subscriber = subscriber
        for child in self._traverse_elements(nested=True):
            child._subscriber = subscriber


class Paragraph(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.P
