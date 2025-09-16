from types import ModuleType
from fastapi import FastAPI, Request
from fastapi.datastructures import Headers
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from schorle.cli import build, generate_models
from schorle.dev import DevManager
from schorle.pages import PagesAccessor, PageReference
import schorle.pages as pages_module
from schorle.render import render
from schorle.utils import cwd, define_if_dev, find_schorle_project
from pathlib import Path
from typing import Union
import msgpack
from fastapi.routing import _merge_lifespan_context


class Schorle:
    def __init__(self, dev: bool | None = None) -> None:
        self.project = find_schorle_project(Path.cwd())

        self._model_registry: list[ModuleType] = []

        self.project.dev = dev if dev is not None else define_if_dev()
        self.dev_manager: DevManager | None = None
        self._pages: PagesAccessor | None = None
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
        self.project._invalidate_page_cache()
        # Also invalidate pages accessor cache
        self._pages = None

    def _generate_models(self):
        for module in self._model_registry:
            generate_models(module_name=module.__name__)

    def add_to_model_registry(self, module: ModuleType):
        self._model_registry.append(module)

    def mount(self, app: FastAPI):
        # mount the static files
        app.mount(
            "/.schorle",
            StaticFiles(directory=self.project.schorle_dir),
            name="schorle",
        )
        # Page infos are now cached at the project level
        # and loaded on-demand in resolve_page_info()

        if self.project.dev:
            # Initialize DevManager once and wire websocket + lifespan
            if self.dev_manager is None:
                self.dev_manager = DevManager(
                    self.project.root_path,
                    reload_callbacks=[
                        self._build,
                        self._generate_models,
                    ],
                )
            app.websocket_route("/_schorle/dev-indicator")(
                self.dev_manager.websocket_endpoint
            )
            app.router.lifespan_context = _merge_lifespan_context(
                app.router.lifespan_context, self.dev_manager.lifespan
            )

    def render(
        self,
        page: Union[Path, PageReference],
        props: dict | BaseModel | None = None,
        req: Request | None = None,
        headers: Headers | None = None,
        cookies: dict[str, str] | None = None,
    ) -> StreamingResponse:
        # Handle PageReference objects by extracting the path
        if isinstance(page, PageReference):
            page_path = page.page_path.relative_to(self.project.pages_path)
        else:
            page_path = page

        page_info = self.project.resolve_page_info(page_path)
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

    @property
    def pages(self) -> PagesAccessor:
        """Access pages using dot notation (e.g., ui.pages.Index, ui.pages.dashboard.About)."""
        if self._pages is None:
            self._pages = pages_module.create_pages_accessor(self.project)
        return self._pages
