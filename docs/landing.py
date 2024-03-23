from pathlib import Path

from starlette.responses import FileResponse, JSONResponse

from schorle.app import Schorle
from schorle.attrs import Classes
from schorle.element import a, div, link
from schorle.icon import icon

app = Schorle(
    extra_assets=[
        link(href="https://fonts.googleapis.com/css?family=Space+Mono", rel="stylesheet", type="text/css"),
    ]
)


def LinkWithIcon(href: str, icon_name: str, additional_text: str) -> a:
    with a(href=href, classes=Classes("btn btn-primary font-normal w-42")) as this:
        this.text(additional_text)
        this >> icon(icon_name)
    return this


LINKS = [
    LinkWithIcon("https://github.com/renardeinside/schorle", "github", "GitHub"),
    LinkWithIcon("https://github.com/renardeinside/schorle/tree/main/examples", "code", "Examples"),
    LinkWithIcon(
        "https://medium.com/@polarpersonal/schorle-testing-the-waters-with-a-python-server-driven-ui-kit-053f85ee6574",
        "book-marked",
        "Concepts",
    ),
]


@app.backend.get("/logo", response_class=FileResponse)
def logo():
    return FileResponse(path=Path(__file__).parent.parent / Path("raw/with_text.svg"), media_type="image/svg+xml")


@app.backend.get("/")
def landing_page():
    with div(
        classes=Classes("flex flex-col justify-center items-center h-screen"), style={"font-family": "Space Mono"}
    ) as mv:
        mv.div(classes=Classes("max-w-screen-md flex flex-col justify-center items-center space-y-4")).img(
            src="/logo",
            alt="Schorle logo",
            media_type="image/svg+xml",
            classes=Classes("w-3/4"),
        )
        mv.p(classes=Classes("text-2xl m-4 p-4 w-5/6 text-center")).text(
            "Pythonic Server-Driven UI Kit for building modern apps."
        )

        mv.div(classes=Classes("flex flex-col space-y-4 space-x-0 md:flex-row md:space-x-4 md:space-y-0")).append(
            *LINKS
        )
    return app.doc.include(mv).to_response()


@app.backend.get("/health", response_class=JSONResponse)
def health():
    return {"status": "ok"}
