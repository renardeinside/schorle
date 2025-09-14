from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from schorle.render import render
from schorle.utils import find_schorle_project
from schorle.manifest import PageInfo
from pathlib import Path
import msgpack


class Schorle:
    def __init__(self) -> None:
        self.project = find_schorle_project(Path.cwd())
        self._page_infos: list[PageInfo] | None = None

    def mount(self, app: FastAPI):
        # mount the static files
        app.mount(
            "/.schorle",
            StaticFiles(directory=self.project.schorle_dir),
            name="schorle",
        )
        # Prepare the list of PageInfo (including js/css) up front from manifest
        # so render calls do not need to re-scan the file system.
        try:
            self._page_infos = self.project.collect_page_infos()
        except Exception:
            # If manifest is missing or build not run yet, keep empty list; callers may handle 404s.
            self._page_infos = []

    def _resolve_page_info(self, page: Path) -> PageInfo:
        if self._page_infos is None:
            self._page_infos = self.project.collect_page_infos()

        # Normalize to project-relative pages path
        if page.is_absolute():
            try:
                rel_to_project = page.relative_to(self.project.project_root)
            except ValueError:
                rel_to_project = page
        else:
            rel_to_project = page

        # If not prefixed with pages/, assume it is relative to pages/
        if rel_to_project.parts and rel_to_project.parts[0] == "pages":
            candidate = Path(*rel_to_project.parts[1:])
        else:
            candidate = rel_to_project

        # Match by filepath under pages (case-sensitive) ignoring extension
        for info in self._page_infos or []:
            rel = info.page.relative_to(self.project.pages_path)
            if rel.with_suffix("") == candidate.with_suffix(""):
                return info

        raise FileNotFoundError(f"Page not found: {page}")

    def render(
        self, page: Path, props: dict | BaseModel | None = None
    ) -> StreamingResponse:
        page_info = self._resolve_page_info(page)
        _bytes = (
            msgpack.packb(props if isinstance(props, dict) else props.model_dump())
            if props is not None
            else None
        )
        return StreamingResponse(
            render(self.project, page_info, _bytes), status_code=200
        )
