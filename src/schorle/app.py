import asyncio
import contextlib
import os
from pathlib import Path
from types import ModuleType
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel
from schorle.dev_watcher import dev_watcher
from schorle.cli import generate_models
from schorle.routes import prepare_router
from schorle.settings import SchorleSettings
from schorle._core import FastClient, ProcessSupervisor, SocketStore
from schorle.token import make_token
from schorle.utils import keys_to_camel_case
from fastapi.responses import StreamingResponse
import msgpack
import secrets
from fastapi.openapi.utils import get_openapi

from schorle.registry import registry


class Schorle:
    def __init__(self, project_root: Path, settings: SchorleSettings | None = None):
        if settings is None:
            settings = SchorleSettings(
                project_root=project_root,
            )
        self.settings = settings
        self._model_registry: list[ModuleType] = []

        self._ipc_secret = secrets.token_hex(32)

        _env = os.environ.copy()
        _env["NODE_ENV"] = "development" if self.settings.dev else "production"
        _env["SCHORLE_JWT_SECRET"] = self._ipc_secret

        self._visor = ProcessSupervisor(
            self.settings.proxy_cmd,
            str(self.settings.schorle_dir),
            _env,
        )
        self._store = SocketStore(
            self.settings.store.socket_path,
            self.settings.store.host,
            self.settings.store.port,
        )

        self._proxy_client = FastClient(
            base_url=f"http://{self.settings.proxy.host}:{self.settings.proxy.port}"
            if self.settings.prefer_http
            else "http://localhost",
            socket_path=self.settings.proxy.socket_path
            if not self.settings.prefer_http
            else None,
        )

        self.router = prepare_router(self._proxy_client, self.settings.dev)

        self._dev_watcher_task: asyncio.Task | None = None

    def _run_generators(self):
        self._generate_registry()
        self._generate_models()

    def _generate_registry(self):
        registry(
            project_root=self.settings.project_root,
            pages=Path("app/pages"),
            ts_out=Path(".schorle/app/registry.gen.tsx"),
            py_out=Path("registry.py"),
            import_prefix="@/pages",
        )

    def _generate_models(self):
        for module in self._model_registry:
            generate_models(module_name=module.__name__)

    async def _wait_for_proxy_ready(self) -> bool:
        print("[schorle] Waiting for proxy to be ready...")
        num_tries = 0
        total_seconds_to_wait = 10
        seconds_to_wait = 0.1
        try:
            while not await self._is_proxy_ready():
                num_tries += 1
                if num_tries > total_seconds_to_wait:
                    print("[schorle] Proxy is not ready after 1 second. Giving up.")
                    raise RuntimeError(
                        "[schorle] Proxy is not ready after 1 second. Giving up."
                    )
                await asyncio.sleep(seconds_to_wait)
                seconds_to_wait *= 2
            print("[schorle] Proxy is ready.")
        except Exception as e:
            print(f"[schorle] Error waiting for proxy to be ready: {e}")
            raise e
        return True

    @contextlib.asynccontextmanager
    async def _lifespan(self):
        next_build_path = self.settings.project_root / ".schorle" / ".next" / "build"

        if not self.settings.dev and not next_build_path.exists():
            raise RuntimeError("Next.js build not found, run `slx build` first")

        if self.settings.dev:
            self._run_generators()
            self._dev_watcher_task = asyncio.create_task(
                dev_watcher(self.settings.project_root / "app", [self._run_generators])
            )

        async with self._visor:
            await self._wait_for_proxy_ready()
            async with self._store:
                try:
                    yield
                finally:
                    if self._dev_watcher_task:
                        self._dev_watcher_task.cancel()

    def add_to_model_registry(self, module: ModuleType):
        self._model_registry.append(module)

    def mount(self, app: FastAPI):
        existing = getattr(app.router, "lifespan_context", None)
        installed = getattr(app.state, "_schorle_lifespan_installed", False)
        if installed:
            print("[schorle] Lifespan already installed.")
            return

        if existing:
            print(f"[schorle] Existing lifespan detected: {bool(existing)}")

            @contextlib.asynccontextmanager
            async def combined(app_):
                async with existing(app_):
                    async with self._lifespan():
                        yield

            app.router.lifespan_context = combined
            app.state._schorle_lifespan_installed = True
            print("[schorle] Lifespan composed and installed.")

        app.include_router(self.router)

    async def _is_proxy_ready(self) -> bool:
        try:
            response = await self._proxy_client.request(
                "GET",
                "/schorle/render",
                headers={"x-schorle-token": make_token(self._ipc_secret)},
            )
            return response.status == 200
        except Exception:
            return False

    async def render(
        self, route_path: str, props: dict | BaseModel | None = None
    ) -> StreamingResponse:
        headers = {}
        headers["x-schorle-token"] = make_token(self._ipc_secret)

        if props is not None:
            props_id = secrets.token_hex(10)
            casted_props = keys_to_camel_case(
                props.model_dump(exclude_unset=True)
                if isinstance(props, BaseModel)
                else props
            )
            self._store.set(props_id, msgpack.packb(casted_props))
            headers["x-schorle-props-id"] = props_id

        # sent GET request to proxy client
        response = await self._proxy_client.request_stream(
            "GET",
            f"{self.settings.proxy.render_endpoint}{route_path}",
            headers=headers,
        )

        async def stream():
            async for chunk in response.aiter_bytes():
                yield chunk

        response_headers = response.headers()
        return StreamingResponse(
            stream(),
            media_type=response_headers.get("content-type"),
            headers=response_headers,
            status_code=response.status,
        )
