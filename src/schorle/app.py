import asyncio
import contextlib
import os
from pathlib import Path
from types import ModuleType

from fastapi import FastAPI
from pydantic import BaseModel
from schorle.cli import generate_models
from schorle.routes import prepare_router
from schorle.settings import SchorleSettings
from schorle._core import FastClient, ProcessSupervisor, SocketStore
from schorle.utils import keys_to_camel_case, lines_printer
from fastapi.responses import StreamingResponse
import msgpack
import secrets


class Schorle:
    def __init__(self, project_root: Path, settings: SchorleSettings | None = None):
        if settings is None:
            settings = SchorleSettings(
                project_root=project_root,
            )
        self.settings = settings
        self._model_registry: list[ModuleType] = []
        os.environ["SCHORLE_FC_LOG"] = "debug"
        os.environ["SCHORLE_STORE_LOG"] = "debug"

        _env = os.environ.copy()
        _env["NODE_ENV"] = "development" if self.settings.dev else "production"
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

        self._stdout_task: asyncio.Task | None = None
        self._stderr_task: asyncio.Task | None = None

        self.router = prepare_router(self._proxy_client)

    def _generate_models(self):
        for module in self._model_registry:
            generate_models(
                project_path=self.settings.project_root, module_name=module.__name__
            )

    async def _wait_for_proxy_ready(self) -> bool:
        print("[schorle] Waiting for proxy to be ready...")
        num_tries = 0
        total_seconds_to_wait = 10
        seconds_to_wait = 0.1
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
        return True

    @contextlib.asynccontextmanager
    async def _lifespan(self):
        async with self._visor:
            async with lines_printer(self._visor.get_stdout_lines, "stdout"):
                async with lines_printer(self._visor.get_stderr_lines, "stderr"):
                    await self._wait_for_proxy_ready()
                    async with self._store:
                        yield

    def add_to_model_registry(self, module: ModuleType):
        self._model_registry.append(module)

    def mount(self, app: FastAPI):
        existing = getattr(app.router, "lifespan_context", None)
        installed = getattr(app.state, "_schorle_lifespan_installed", False)
        if installed:
            print("[schorle] Lifespan already installed.")
            return

        if existing:
            print("[schorle] Existing lifespan detected: {bool(existing)}")

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
            response = await self._proxy_client.request("GET", "/schorle/render")
            return response.status == 200
        except Exception:
            return False

    async def render(
        self, route_path: str, props: dict | BaseModel | None = None
    ) -> StreamingResponse:
        headers = {}
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
