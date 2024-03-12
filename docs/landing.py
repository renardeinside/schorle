from functools import partial
from pathlib import Path

from pydantic import Field
from starlette.responses import FileResponse, JSONResponse

from schorle.app import Schorle
from schorle.attrs import Classes
from schorle.element import a, div, link, p
from schorle.icon import Icon
from schorle.img import Image
from schorle.page import Page
from schorle.text import text

app = Schorle(
    extra_assets=[
        partial(link, href="https://fonts.googleapis.com/css?family=Space+Mono", rel="stylesheet", type="text/css"),
    ]
)


def LinkWithIcon(href: str, icon_name: str, additional_text: str) -> None:
    with a(href=href, classes=Classes("btn btn-primary font-normal w-42")):
        text(additional_text)
        Icon(name=icon_name)


LINKS_INFO = [
    ("https://github.com/renardeinside/schorle", "github", "GitHub"),
    ("https://github.com/renardeinside/schorle/tree/main/examples", "code", "Examples"),
    (
        "https://medium.com/@polarpersonal/schorle-testing-the-waters-with-a-python-server-driven-ui-kit-053f85ee6574",
        "book-marked",
        "Concepts",
    ),
]


@app.backend.get("/logo", response_class=FileResponse)
def logo():
    return FileResponse(path=Path(__file__).parent.parent / Path("raw/with_text.svg"), media_type="image/svg+xml")


class LandingPage(Page):
    style: dict[str, str] = Field(default_factory=lambda: {"font-family": "Space Mono"})

    def render(self):
        with div(classes=Classes("flex flex-col justify-center items-center h-screen")):
            with div(classes=Classes("max-w-screen-md flex flex-col justify-center items-center space-y-4")):
                Image(
                    src="/logo",
                    alt="Schorle logo",
                    media_type="image/svg+xml",
                    classes=Classes("w-3/4"),
                )
            with p(classes=Classes("text-2xl m-4 p-4 w-5/6 text-center")):
                text("Pythonic Server-Driven UI Kit for building modern apps.")

            with div(classes=Classes("flex flex-col space-y-4 space-x-0 md:flex-row md:space-x-4 md:space-y-0")):
                for info in LINKS_INFO:
                    LinkWithIcon(*info)


@app.get("/")
def landing_page():
    return LandingPage()


@app.backend.get("/health", response_class=JSONResponse)
def health():
    return {"status": "ok"}
