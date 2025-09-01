from pathlib import Path
from pydantic import BaseModel, PrivateAttr
from schorle.cli import build
from schorle.render import render
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import inspect


class Schorle(BaseModel):
    _init_path: Path | None = PrivateAttr(None)  # private field to store caller path

    def __init__(self, **data):
        super().__init__(**data)
        # Inspect call stack: frame[0] = current, frame[1] = caller of __init__
        frame = inspect.stack()[1]
        self._init_path = Path(frame.filename).resolve().parent

    @property
    def root_path(self) -> Path:
        return self._init_path

    def build(self) -> None:
        build(self.root_path)

    @property
    def dist_path(self) -> Path:
        return self.root_path / ".schorle" / "dist"

    def render(self, page_name: str) -> str:
        return render(self.root_path, page_name)

    def to_response(self, page_name: str) -> HTMLResponse:
        return HTMLResponse(content=self.render(page_name), media_type="text/html")

    def static_files(self) -> StaticFiles:
        return StaticFiles(directory=self.dist_path)
