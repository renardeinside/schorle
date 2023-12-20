from typing import Annotated, Union

from pydantic import Field
from starlette.responses import HTMLResponse

from schorle.elements.base import Element, ElementWithGeneratedId
from schorle.elements.tags import HTMLTag
from schorle.theme import Theme


class Meta(Element):
    tag: HTMLTag = HTMLTag.META
    charset: str = Field(None, attribute=True)
    name: str = Field(None, attribute=True)
    content: str = Field(None, attribute=True)


class Title(Element):
    tag: HTMLTag = HTMLTag.TITLE
    text: str = "Schorle"


class Link(Element):
    tag: HTMLTag = HTMLTag.LINK
    href: str = Field(..., attribute=True)
    rel: str = Field(..., attribute=True)
    type_: str = Field(..., attribute=True, alias="type")


class Script(Element):
    tag: HTMLTag = HTMLTag.SCRIPT
    src: str = Field(..., attribute=True)
    crossorigin: str = Field(None, attribute=True)
    text: str = ""


class Head(Element):
    tag: HTMLTag = HTMLTag.HEAD
    charset_meta: Meta = Field(default_factory=Meta.factory(charset="utf-8"))
    viewport_meta: Annotated[
        Meta, Field(default_factory=Meta.factory(name="viewport", content="width=device-width, initial-scale=1"))
    ]
    title: Annotated[Title, Field(default_factory=Title)]
    bundle: Annotated[
        Script, Field(default_factory=Script.factory(src="/_schorle/assets/bundle.js", crossorigin="anonymous"))
    ]
    daisy_ui: Annotated[
        Link,
        Field(
            default_factory=Link.factory(
                href="https://cdn.jsdelivr.net/npm/daisyui@4.4.22/dist/full.min.css",
                rel="stylesheet",
                type="text/css",
            )
        ),
    ]
    tailwind: Annotated[Script, Field(default_factory=Script.factory(src="https://cdn.tailwindcss.com"))]


class Body(Element):
    tag: HTMLTag = HTMLTag.BODY


class Html(Element):
    tag: HTMLTag = HTMLTag.HTML
    theme: Theme = Field(default=Theme.DARK, attribute=True, alias="data-theme")
    head: Annotated[Head, Field(default_factory=Head)]
    body: Annotated[Body, Field(default_factory=Body)]


class Div(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.DIV


class Button(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.BUTTON


class Span(ElementWithGeneratedId):
    tag: HTMLTag = HTMLTag.SPAN


class BodyWithPage(Body):
    content: "Page"


class DeveloperTools(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-developer-tools"
    hx_ws: str = Field(attribute=True, default="connect:/_schorle/devtools", alias="hx-ws")


class BodyWithPageAndDeveloperTools(BodyWithPage):
    developer_tools: "DeveloperTools" = Field(default_factory=DeveloperTools)


class Page(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    def render_to_response(
        self, body_class: Union[type[BodyWithPage], type[BodyWithPageAndDeveloperTools]] = BodyWithPage
    ) -> HTMLResponse:
        html = Html(body=body_class(content=self))
        response = HTMLResponse(html.render(), status_code=200)
        return response
