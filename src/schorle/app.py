import asyncio
import contextlib
import json
import os
from pathlib import Path
import secrets
from typing import AsyncIterator, Mapping, Optional

import aiohttp
import httpx
from fastapi import APIRouter
from fastapi.concurrency import asynccontextmanager
from starlette.responses import StreamingResponse

from schorle.ipc_manager import IpcManager
from schorle.dev_extension import DevExtension
from schorle.settings import SchorleSettings, IpcSettings
from schorle.store import SocketStore


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
            raise ValueError(f"Project root is not a directory: {self.project_root}")
        if not (self.project_root / ".schorle").is_dir():
            raise ValueError(
                f"Project root does not have a .schorle directory: {self.project_root}"
            )
        if ipc is None:
            ipc = IpcSettings(
                bun_cmd=("bun", "run", "server.ts"),
                socket_path=None,
                ready_check_url="/",
            )
        self.cwd = self.project_root / ".schorle"

        if cfg is None:
            cfg = SchorleSettings()

        # Upstream/paths
        self.upstream_host = cfg.upstream_host
        self.base_http = cfg.base_http
        self.upstream_ws_path = cfg.upstream_ws_path

        # Lifecycle clients (initialized during startup)
        self._http: Optional[httpx.AsyncClient] = None
        self._ws: Optional[aiohttp.ClientSession] = None

        self._store_socket_path = Path(f"/tmp/slx-store-{secrets.token_hex(8)}.sock")

        # IPC supervisor
        self.ipc = IpcManager(
            cwd=self.cwd,
            bun_cmd=ipc.bun_cmd,
            socket_path=ipc.socket_path,
            store_socket_path=str(self._store_socket_path),
            base_http=self.base_http,
            ready_check_url=ipc.ready_check_url,
            ready_timeout_s=ipc.ready_timeout_s,
            retry_base_delay_s=ipc.retry_base_delay_s,
            retry_max_delay_s=ipc.retry_max_delay_s,
            upstream_host=self.upstream_host,
        )

        self.store = SocketStore(self._store_socket_path)

        # Root router; feature routers can be included under it
        self.router = APIRouter()

        # Dev-only extension (HMR WS, asset proxy, dev-indicator)
        self.dev: Optional[DevExtension] = None
        if cfg.enable_dev_extension:
            self.dev = DevExtension(
                upstream_host=self.upstream_host,
                upstream_ws_path=self.upstream_ws_path,
                mount_assets_proxy=cfg.mount_assets_proxy,
                ensure_http=self._ensure_http,
                render=self.render,
                get_ws_session=self._get_ws_session,
            )
            self.router.include_router(self.dev.router)

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
    ) -> StreamingResponse:
        if not route_path.startswith("/"):
            route_path = "/" + route_path

        client = await self._ensure_http("render")
        url = f"{self.base_http}{route_path}"
        if query_string:
            url += f"?{query_string}"

        in_headers = dict(headers or {})
        in_headers.setdefault("host", self.upstream_host)

        if props is not None:
            store_id = secrets.token_hex(20)
            self.store.set(store_id, json.dumps(props))
            in_headers["x-schorle-store-id"] = store_id

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

    async def _on_shutdown(self):
        await self.ipc.stop()
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
