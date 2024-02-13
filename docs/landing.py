from __future__ import annotations

from functools import partial
from pathlib import Path

from pydantic import Field

from schorle.app import Schorle
from schorle.classes import Classes
from schorle.element import a, div, img, link, p
from schorle.icon import Icon
from schorle.page import Page
from schorle.text import text

app = Schorle(
    extra_assets=[
        partial(link, href="https://fonts.googleapis.com/css?family=Space+Mono"),
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


class LandingPage(Page):
    style: dict[str, str] = Field(default_factory=lambda: {"font-family": "Space Mono"})

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            with div(classes=Classes("max-w-screen-md flex flex-col justify-center items-center space-y-4")):
                img(
                    src=Path(__file__).parent.parent / Path("raw/with_text.svg"),
                    alt="Schorle logo",
                    mime_type="image/svg+xml",
                    classes=Classes("max-w-md m-4"),
                )
            with p(classes=Classes("text-2xl font-bold p-4 w-5/6 text-center")):
                text("Pythonic Server-Driven UI Kit for building modern apps.")

            with div(classes=Classes("flex flex-col space-y-4 md:flex-row md:space-y-0 md:space-x-4")):
                for href, icon, _text in LINKS:
                    with a(href=href, classes=Classes("btn btn-primary font-normal")):
                        text(_text)
                        icon.add()


@app.get("/")
def landing_page():
    return LandingPage()
