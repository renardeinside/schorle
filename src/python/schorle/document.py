import base64
import hashlib
from typing import Callable

from fastapi.responses import HTMLResponse
from lxml import etree
from pydantic import Field

from schorle.component import Component
from schorle.element import body, div, head, link, meta, script, span, title
from schorle.rendering_context import rendering_context
from schorle.session import Session
from schorle.tags import HTMLTag
from schorle.text import text
from schorle.theme import Theme
from schorle.utils import ASSETS_PATH


class DevLoader(Component):
    element_id: str = "dev-loader"
    classes: str = "absolute bottom-4 right-4 hidden"

    def render(self):
        span(classes="loading loading-md loading-bars text-primary")


def get_integrity(raw_file_path: str) -> str:
    file_path = ASSETS_PATH / raw_file_path
    if not file_path.exists():
        msg = f"File '{file_path}' not found."
        raise FileNotFoundError(msg)

    # Open the file in binary mode for reading
    with open(file_path, "rb") as f:
        # Calculate the SHA384 hash of the file
        hash_obj = hashlib.sha256()
        while True:
            # Read the file in chunks to avoid loading large files into memory
            chunk = f.read(4096)
            if not chunk:
                break
            hash_obj.update(chunk)

    # Encode the hash using base64 with URL and filename safe characters
    integrity_hash = base64.b64encode(hash_obj.digest()).decode()

    # Prepend "sha384-" to the hash
    return f"sha256-{integrity_hash}"


class Document(Component):
    page: Component
    title: str = "Schorle"
    theme: Theme
    extra_assets: Callable[..., None] | None = None
    lang: str = "en"
    with_dev_tools: bool = False
    body_attrs: dict[str, str] | None = Field(default_factory=dict)
    tag: HTMLTag = HTMLTag.HTML

    def __init__(self, **data):
        super().__init__(**data)
        self.element_id = None
        self.attrs = {"data-theme": self.theme.value, "lang": self.lang}

    def render(self):
        with head():
            meta(charset="utf-8")
            meta(name="viewport", content="width=device-width, initial-scale=1.0")

            with title():
                text(self.title)

            if self.with_dev_tools:
                meta(name="schorle-dev-mode", content="true")

            link(href="/favicon.svg", rel="icon", type="image/svg+xml")

            script(
                src="/_schorle/dist/tailwind.min.js.br",
                integrity=get_integrity("dist/tailwind.min.js"),
                crossorigin="anonymous",
            )
            link(
                href="/_schorle/dist/daisyui.min.css.br",
                integrity=get_integrity("dist/daisyui.min.css"),
                crossorigin="anonymous",
                rel="stylesheet",
            )
            script(
                src="/_schorle/js/index.min.js.br",
                integrity=get_integrity("js/index.min.js"),
                crossorigin="anonymous",
                defer="",
                **{"type": "module"},
            )
            if self.extra_assets:
                self.extra_assets()

        with body(**self.body_attrs):
            with div(element_id="schorle-page"):
                self.page()

            if self.with_dev_tools:
                DevLoader()

    def to_response(self, session: Session) -> HTMLResponse:
        with rendering_context(root=self) as rc:
            self.render()
        return HTMLResponse(
            etree.tostring(rc.to_lxml(session), pretty_print=True).decode("utf-8"),
            200,
        )
