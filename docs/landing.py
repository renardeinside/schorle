from pathlib import Path

from pydantic import BaseModel
from starlette.responses import FileResponse, JSONResponse

from schorle.app import Schorle
from schorle.component import Component
from schorle.element import div, img, link, span
from schorle.icon import icon
from schorle.tags import HTMLTag
from schorle.text import text


def extra_assets():
    link(href="https://fonts.googleapis.com/css?family=Space+Mono", rel="stylesheet", type="text/css")


app = Schorle(extra_assets=extra_assets)


class LinkProps(BaseModel):
    href: str
    icon: str
    text: str


class LinkWithIcon(Component):
    tag: HTMLTag = HTMLTag.A
    props: LinkProps
    classes: str = "btn btn-primary font-normal w-42"

    def initialize(self):
        self.attrs["href"] = self.props.href

    def render(self):
        icon(self.props.icon)
        with span():
            text(self.props.text)


LINKS = [
    LinkWithIcon(props=LinkProps(href="https://github.com/renardeinside/schorle", icon="github", text="GitHub")),
    LinkWithIcon(
        props=LinkProps(
            href="https://github.com/renardeinside/schorle/tree/main/examples", icon="code", text="Examples"
        )
    ),
    LinkWithIcon(
        props=LinkProps(
            href="https://medium.com/@polarpersonal/schorle-testing-the-waters-with-a-python-server-driven-ui-kit-053f85ee6574",
            icon="book-marked",
            text="Concepts",
        )
    ),
]


class LandingPage(Component):
    def render(self):
        with div(classes="flex flex-col justify-center items-center h-screen", style={"font-family": "Space Mono"}):
            with div(classes="max-w-screen-md flex flex-col justify-center items-center space-y-4"):
                img(
                    src="/logo",
                    alt="Schorle logo",
                    media_type="image/svg+xml",
                    classes="w-3/4",
                )
            with span(classes="text-2xl m-4 p-4 w-5/6 text-center"):
                text("Pythonic Server-Driven UI Kit for building modern apps.")

            with div(classes="flex flex-col space-y-4 space-x-0 md:flex-row md:space-x-4 md:space-y-0"):
                for link_item in LINKS:
                    link_item()


@app.get("/")
def landing_page():
    return LandingPage()


@app.backend.get("/health", response_class=JSONResponse)
def health():
    return {"status": "ok"}


@app.backend.get("/logo", response_class=FileResponse)
def logo():
    return FileResponse(path=Path(__file__).parent.parent / Path("raw/with_text.svg"), media_type="image/svg+xml")
