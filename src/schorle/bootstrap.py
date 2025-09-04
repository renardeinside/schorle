from pathlib import Path
from fastapi import FastAPI
from schorle.cli import build
from fastapi.staticfiles import StaticFiles


def bootstrap(project_path: Path, dist_path: Path, app: FastAPI):
    build(project_path)
    app.mount("/.schorle/dist", StaticFiles(directory=dist_path))
