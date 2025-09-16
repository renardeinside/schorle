from fastapi import FastAPI, Request
from fastapi.datastructures import Headers
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from schorle.cli import build
from schorle.dev import DevManager
from schorle.render import render
from schorle.utils import cwd, define_if_dev, find_schorle_project
from schorle.manifest import PageInfo
from pathlib import Path
import msgpack
from fastapi.routing import _merge_lifespan_context


class Schorle:
    def __init__(self, dev: bool | None = None) -> None:
        self.project = find_schorle_project(Path.cwd())
        self.project.dev = dev if dev is not None else define_if_dev()
        self._page_infos: list[PageInfo] | None = None
        self.dev_manager: DevManager | None = None
        print(f"[schorle] running in {'dev' if self.project.dev else 'prod'} mode")
        if not self.project.dev:
            # check if the manifest exists, raise an error if it doesn't
            if not self.project.manifest_path.exists():
                raise RuntimeError(
                    "Cannot run in prod mode without a build. Please run `slx build`."
                )

    def _build(self):
        with cwd(self.project.root_path):
            build(dev=self.project.dev)
        # Invalidate cached page info after build to pick up new manifest
        self._invalidate_cache()

    def _invalidate_cache(self):
        """Invalidate cached page info to force fresh reads from the manifest."""
        self._page_infos = None

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

        if self.project.dev:
            # Initialize DevManager once and wire websocket + lifespan
            if self.dev_manager is None:
                self.dev_manager = DevManager(self.project.root_path, [self._build])
            app.websocket_route("/_schorle/dev-indicator")(
                self.dev_manager.websocket_endpoint
            )
            app.router.lifespan_context = _merge_lifespan_context(
                app.router.lifespan_context, self.dev_manager.lifespan
            )

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
        self,
        page: Path,
        props: dict | BaseModel | None = None,
        req: Request | None = None,
        headers: Headers | None = None,
        cookies: dict[str, str] | None = None,
    ) -> StreamingResponse:
        page_info = self._resolve_page_info(page)
        _bytes = (
            msgpack.packb(props if isinstance(props, dict) else props.model_dump())
            if props is not None
            else None
        )

        if req is not None:
            headers = headers or req.headers
            cookies = cookies or req.cookies
        else:
            headers = headers or Headers()
            cookies = cookies or {}

        return StreamingResponse(
            render(self.project, page_info, _bytes, headers, cookies), status_code=200
        )
