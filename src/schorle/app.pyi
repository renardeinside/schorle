# Auto-generated stub file for Schorle app module
# This provides type checking for ui.pages access

from typing import Union
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.datastructures import Headers
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from schorle.pages import PagesAccessor, PageReference

class Schorle:
    def __init__(self, dev: bool | None = None) -> None: ...
    def mount(self, app: FastAPI) -> None: ...
    def render(
        self,
        page: Union[Path, PageReference],
        props: dict | BaseModel | None = None,
        req: Request | None = None,
        headers: Headers | None = None,
        cookies: dict[str, str] | None = None,
    ) -> StreamingResponse: ...
    @property
    def pages(self) -> PagesAccessor: ...
