from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from schorle.render import render
from schorle.utils import find_schorle_project


class Schorle:
    def __init__(self):
        self.project = find_schorle_project(Path.cwd())

    def mount(self, app: FastAPI):
        # mount the static files
        app.mount(
            "/.schorle",
            StaticFiles(directory=self.project.dist_path),
            name="schorle",
        )

    def render(self, page: Path) -> StreamingResponse:
        return StreamingResponse(render(self.project, page), status_code=200)
