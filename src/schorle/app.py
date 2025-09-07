import asyncio
import contextlib
import os
from functools import partial
from pathlib import Path
import secrets
from typing import AsyncIterator, Mapping, Optional

import aiohttp
import httpx
from fastapi import APIRouter, FastAPI
from fastapi.concurrency import asynccontextmanager
from starlette.responses import StreamingResponse

from schorle.bun import check_and_prepare_bun
from schorle.ipc_manager import IpcManager
from schorle.dev_extension import DevExtension
from schorle.settings import SchorleSettings, IpcSettings
from schorle.store import SocketStore
import msgpack
import subprocess
from schorle.utils import keys_to_camel_case
from fastapi.staticfiles import StaticFiles


class Schorle:
    """
    Core UDS HTTP client & lifecycle manager.
    - Supervises Bun via IpcManager
    - Streams HTTP to upstream over UDS
    - Exposes helpers consumed by DevExtension (optional)
    """

    def __init__(
        self,
        project_root: str | os.PathLike | Path = ".",
        cfg: SchorleSettings = None,
        ipc: IpcSettings | None = None,
    ):
        # Validate & derive paths
        self.project_root = Path(project_root)

        if not self.project_root.is_dir():
            raise ValueError(
                f"Project root {self.project_root.absolute()} is not a directory"
            )
        if not (self.project_root / ".schorle").is_dir():
            raise ValueError(
                f"Project root does not have a .schorle subdirectory: {self.project_root.absolute()}"
            )

        self.bun_executable = check_and_prepare_bun()

        self._store_socket_path = Path(f"/tmp/slx-store-{secrets.token_hex(8)}.sock")
        self._socket_path = Path(f"/tmp/slx-{secrets.token_hex(8)}.sock")

        if ipc is None:
            ipc = IpcSettings(
                bun_cmd=(self.bun_executable, "run", "server.ts"),
                socket_path=str(self._socket_path),
                ready_check_url="/schorle/render",
                store_socket_path=str(self._store_socket_path),
            )
        self.cwd = self.project_root / ".schorle"

        if cfg is None:
            self.cfg = SchorleSettings()
        else:
            self.cfg = cfg

        # Upstream/paths
        self.upstream_host = self.cfg.upstream_host
        self.base_http = self.cfg.base_http
        self.upstream_ws_path = self.cfg.upstream_ws_path

        # Lifecycle clients (initialized during startup)
        self._http: Optional[httpx.AsyncClient] = None
        self._ws: Optional[aiohttp.ClientSession] = None

        if self.cfg.enable_dev_extension:
            print("[schorle] Is running in development mode")
        else:
            print("[schorle] Is running in production mode")

            # check if project_root/.schorle/.next/build exists
            if not (self.project_root / ".schorle" / ".next" / "build").exists():
                print("[schorle] Build directory does not exist - running build script")
                subprocess.run(
                    [self.bun_executable, "run", "build"],
                    cwd=self.project_root / ".schorle",
                )
                print("[schorle] Running build script - finished")
            else:
                print("[schorle] Build directory exists - skipping build script")
            ipc.env = {"NODE_ENV": "production"}

        # IPC supervisor
        self.ipc = IpcManager(
            cwd=self.cwd,
            bun_cmd=ipc.bun_cmd,
            socket_path=ipc.socket_path,
            store_socket_path=ipc.store_socket_path,
            base_http=self.base_http,
            ready_check_url=ipc.ready_check_url,
            ready_timeout_s=ipc.ready_timeout_s,
            retry_base_delay_s=ipc.retry_base_delay_s,
            retry_max_delay_s=ipc.retry_max_delay_s,
            upstream_host=self.upstream_host,
            with_bun_logs=ipc.with_bun_logs,
            env=ipc.env,
        )

        self.store = SocketStore(ipc.store_socket_path)

        # Root router; feature routers can be included under it
        self.router = APIRouter()

        # Dev-only extension (HMR WS, asset proxy, dev-indicator)
        self.dev: Optional[DevExtension] = None
        if self.cfg.enable_dev_extension:
            self.dev = DevExtension(
                project_root=self.project_root,
                upstream_host=self.upstream_host,
                upstream_ws_path=self.upstream_ws_path,
                mount_assets_proxy=self.cfg.mount_assets_proxy,
                ensure_http=self._ensure_http,
                render=partial(self.render, add_prefix=False),
                get_ws_session=self._get_ws_session,
            )
            self.router.include_router(self.dev.router)

    def _wire_production_routes(self, app: FastAPI):
        next_files_path = self.project_root / ".schorle" / ".next"
        print(f"[schorle] Wiring production routes to {next_files_path} ")
        app.mount(
            "/_next",
            StaticFiles(directory=next_files_path),
        )
        print("[schorle] Production routes wired.")

    # ---------- public API ----------

    def mount(self, app):
        """
        Attach routes and compose our lifespan with the app's existing lifespan (if any).
        """
        if getattr(app.state, "_schorle_lifespan_installed", False):
            print(
                "[schorle] mount() called again — skipping lifespan wiring (already installed)."
            )
        else:
            existing = getattr(app.router, "lifespan_context", None)
            print(f"[schorle] Existing lifespan detected: {bool(existing)}")

            @asynccontextmanager
            async def combined(app_):
                if existing:
                    print("[schorle] Entering combined lifespan: existing -> schorle")
                    async with existing(app_):
                        async with self._lifespan_cm(app_):
                            yield
                    print("[schorle] Exited combined lifespan: schorle -> existing")
                else:
                    print("[schorle] Entering schorle lifespan (no existing lifespan).")
                    async with self._lifespan_cm(app_):
                        yield
                    print("[schorle] Exited schorle lifespan.")

            app.router.lifespan_context = combined
            app.state._schorle_lifespan_installed = True
            print("[schorle] Lifespan composed and installed.")

            if not self.cfg.enable_dev_extension:
                self._wire_production_routes(app)

        if not getattr(app.state, "_schorle_routes_mounted", False):
            app.include_router(self.router)
            app.state._schorle_routes_mounted = True
            print("[schorle] Router mounted.")
        else:
            print("[schorle] Router already mounted — skipping.")

    @contextlib.asynccontextmanager
    async def _lifespan_cm(self, app):
        try:
            await self._on_startup()
            yield
        finally:
            await self._on_shutdown()

    async def render(
        self,
        route_path: str,
        *,
        method: str = "GET",
        headers: Optional[Mapping[str, str]] = None,
        body_stream: Optional[AsyncIterator[bytes]] = None,
        query_string: Optional[str] = None,
        props: Optional[dict] = None,
        add_prefix: bool = True,
    ) -> StreamingResponse:
        if not route_path.startswith("/"):
            route_path = "/" + route_path

        client = await self._ensure_http("render")
        url = (
            f"{self.base_http}/schorle/render{route_path}"
            if add_prefix
            else f"{self.base_http}{route_path}"
        )
        if query_string:
            url += f"?{query_string}"

        in_headers = dict(headers or {})
        in_headers.setdefault("host", self.upstream_host)

        if props is not None:
            props_id = secrets.token_hex(10)
            casted_props = keys_to_camel_case(props)
            self.store.set(props_id, msgpack.packb(casted_props))
            in_headers["x-schorle-props-id"] = props_id

        req = client.build_request(
            method=method,
            url=url,
            headers=in_headers,
            content=body_stream if method not in ("GET", "HEAD") else None,
        )
        upstream_resp = await client.send(req, stream=True)

        async def upstream_iter() -> AsyncIterator[bytes]:
            try:
                async for chunk in upstream_resp.aiter_raw():
                    yield chunk
            finally:
                await upstream_resp.aclose()

        out_headers = dict(upstream_resp.headers)
        out_headers.pop("content-length", None)
        for k in list(out_headers):
            if k.lower() in {
                "connection",
                "proxy-connection",
                "keep-alive",
                "te",
                "trailer",
                "transfer-encoding",
                "upgrade",
            }:
                out_headers.pop(k, None)

        return StreamingResponse(
            upstream_iter(),
            status_code=upstream_resp.status_code,
            headers=out_headers,
            media_type=upstream_resp.headers.get("content-type"),
        )

    # ---------- lifecycle ----------

    async def _on_startup(self):
        await self.store.start()

        self._http = httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(uds=self.ipc.socket_path),
            timeout=None,
            http2=False,
        )
        self._ws = aiohttp.ClientSession(
            connector=aiohttp.UnixConnector(path=self.ipc.socket_path)
        )

        await self.ipc.start()
        await self.ipc.wait_until_ready()

        if self.dev:
            self.dev.start_watcher()

    async def _on_shutdown(self):
        try:
            await self.ipc.stop()
            if self.dev:
                self.dev.stop_watcher()
        except Exception as e:
            print(f"[schorle] Error stopping IPC: {e}")
        await self.store.stop()

        if self._http:
            await self._http.aclose()
        if self._ws:
            await self._ws.close()
        self._http = None
        self._ws = None

    # ---------- internals ----------

    async def _ensure_http(self, initiator: str = "unknown") -> httpx.AsyncClient:
        while not self.ipc.is_ready:
            print(f"⏳ Waiting for server to be ready... (initiated by {initiator})")
            await asyncio.sleep(0.1)
        assert self._http is not None, "HTTP client not initialized"
        return self._http

    def _get_ws_session(self) -> aiohttp.ClientSession:
        assert self._ws is not None, "WS client not initialized"
        return self._ws
