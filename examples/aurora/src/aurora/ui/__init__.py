# Generated file — do not edit manually

from pathlib import Path
from fastapi.responses import HTMLResponse
from schorle.render import render
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

root_path = Path(__file__).parent
dist_path = root_path / ".schorle" / "dist"


def mount_assets(app: FastAPI):
    app.mount("/.schorle/dist", StaticFiles(directory=dist_path))


class Index:
    @classmethod
    def render(cls) -> str:
        return render(root_path, "Index")

    @classmethod
    def to_response(cls) -> HTMLResponse:
        return HTMLResponse(content=cls.render(), media_type="text/html")
