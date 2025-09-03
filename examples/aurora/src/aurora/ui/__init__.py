# Generated file — do not edit manually

from pathlib import Path
from fastapi.responses import HTMLResponse
from schorle.render import render
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from schorle.cli import build

root_path = Path(__file__).parent
dist_path = root_path / ".schorle" / "dist"


def mount_assets(app: FastAPI):
    build(root_path)
    app.mount("/.schorle/dist", StaticFiles(directory=dist_path))


def Counter() -> HTMLResponse:
    return HTMLResponse(content=render(root_path, "Counter"), media_type="text/html")


def Index() -> HTMLResponse:
    return HTMLResponse(content=render(root_path, "Index"), media_type="text/html")
