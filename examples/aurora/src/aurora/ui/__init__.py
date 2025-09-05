# Generated file — do not edit manually

from pathlib import Path
from schorle.render import render_to_stream
from fastapi.responses import StreamingResponse
from fastapi import FastAPI
from functools import partial
from schorle.bootstrap import bootstrap as _base_bootstrap
from typing import Callable

project_path = Path(__file__).parent
dist_path = project_path / ".schorle" / "dist"
bootstrap: Callable[[FastAPI], None] = partial(_base_bootstrap, project_path, dist_path)


def Index() -> StreamingResponse:
    return render_to_stream(project_path, "Index")
