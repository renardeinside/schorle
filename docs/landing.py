from __future__ import annotations

from pathlib import Path

from pydantic import Field

from schorle.app import Schorle
from schorle.elements.html import Div, HeadLink
from schorle.elements.icon import Icon
from schorle.elements.img import Img
from schorle.elements.link import Link
from schorle.elements.page import Page
from schorle.reactives.classes import Classes

app = Schorle(
    extra_assets=[
        HeadLink(rel="stylesheet", href="https://fonts.googleapis.com/css?family=Space+Mono"),
    ]
)

LINKS = [
    ("https://github.com/renardeinside/schorle", Icon(name="github"), "GitHub"),
    ("https://github.com/renardeinside/schorle/tree/main/examples", Icon(name="code"), "Examples"),
    (
        "https://medium.com/@polarpersonal/schorle-testing-the-waters-with-a-python-server-driven-ui-kit-053f85ee6574",
        Icon(name="book"),
        "Concepts",
    ),
]

ImageContainer = Div.derive(
    classes=Classes("max-w-md m-4"),
    image=Img.factory(
        file_path=Path(__file__).parent.parent / Path("raw/with_text.svg"),
        alt="Schorle logo",
        mime_type="image/svg+xml",
    ),
)

Headline = Div.derive(
    classes=Classes("text-2xl font-bold p-4 w-5/6 text-center"),
    text="""Pythonic Server-Driven UI Kit for building modern apps.""",
)

LinkWithIcon = Link.derive(icon=Icon.factory())

wrapped_links = [
    LinkWithIcon(href=link, icon=icon, text=text, classes=Classes("btn btn-primary")) for link, icon, text in LINKS
]

Buttons = Div.derive(
    classes=(Classes, Classes("flex flex-col space-y-4 md:flex-row md:space-y-0 md:space-x-4")),
    buttons=(list[LinkWithIcon], Field(default_factory=lambda: wrapped_links)),
)

Content = Div.derive(
    classes=Classes("max-w-screen-md flex flex-col justify-center items-center h-5/6 space-y-4"),
    image_container=ImageContainer.factory(),
    headline=Headline.factory(),
    buttons=Buttons.factory(),
)

ContentWrapper = Div.derive(
    classes=Classes("flex flex-col justify-center items-center h-screen"), content=Content.factory()
)


class LandingPage(Page):
    style: dict[str, str] = Field(default_factory=lambda: {"font-family": "Space Mono"})
    classes: Classes = Classes("w-full h-full")
    content_wrapper: ContentWrapper = ContentWrapper.factory()


@app.get("/")
def landing_page():
    return LandingPage()
