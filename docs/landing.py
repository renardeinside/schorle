from pathlib import Path

from pydantic import Field

from schorle.app import Schorle
from schorle.elements.html import Div, HeadLink
from schorle.elements.icon import Icon
from schorle.elements.img import Img
from schorle.elements.link import Link
from schorle.elements.page import Page
from schorle.reactives.classes import Classes

app = Schorle(extra_assets=[HeadLink(rel="stylesheet", href="https://fonts.googleapis.com/css?family=Space+Mono")])


def logo_with_text() -> Img:
    # path relative to the current file
    _path = Path(__file__).parent.parent / Path("raw/with_text.svg")
    return Img.from_file(_path, alt="Schorle logo", mime_type="svg+xml")


class LogoContainer(Div):
    classes: Classes = Classes("w-10")
    logo: Img


def logo_without_text() -> LogoContainer:
    # path relative to the current file
    _path = Path(__file__).parent.parent / Path("raw/logo.svg")
    container = LogoContainer(logo=Img.from_file(_path, alt="Schorle logo", mime_type="svg+xml"))
    return container


class ImageContainer(Div):
    classes: Classes = Classes("max-w-md m-4")
    image: Img = Field(default_factory=logo_with_text)


class Headline(Div):
    classes: Classes = Classes("text-2xl font-bold p-4 w-5/6 text-center")
    text: str = """Pythonic Server-Driven UI Kit for building modern apps."""


class Navbar(Div):
    _base_classes: Classes = Classes("navbar bg-base-300")
    logo: Div = Field(default_factory=logo_without_text)


LINKS = [
    ("https://github.com/renardeinside/schorle", f"{Icon(name='github')} GitHub"),
    ("https://github.com/renardeinside/schorle/tree/main/examples", f"{Icon(name='code')} Examples"),
    (
        "https://medium.com/@polarpersonal/schorle-testing-the-waters-with-a-python-server-driven-ui-kit-053f85ee6574",
        f"{Icon(name='book')} Concepts",
    ),
]


class Buttons(Div):
    classes: Classes = Classes("flex space-x-4")
    buttons: list[Link] = Field(
        default_factory=lambda: [Link(href=link, text=text, classes=Classes("btn btn-primary")) for link, text in LINKS]
    )


class Content(Div):
    classes: Classes = Classes("max-w-screen-md flex flex-col justify-center items-center h-5/6 space-y-4")
    image_container: ImageContainer = ImageContainer.factory()
    headline: Headline = Headline.factory()
    buttons: Buttons = Buttons.factory()


class ContentWrapper(Div):
    classes: Classes = Classes("flex flex-col justify-center items-center")
    content: Content = Content.factory()


class LandingPage(Page):
    style: dict[str, str] = Field(default_factory=lambda: {"font-family": "Space Mono"})
    classes: Classes = Classes("mx-auto w-full h-full")
    navbar: Navbar = Navbar.factory()
    content_wrapper: ContentWrapper = ContentWrapper.factory()


@app.get("/")
def landing_page():
    return LandingPage()
