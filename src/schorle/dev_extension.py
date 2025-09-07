# --- dev_extension.py (new DevExtension) ---

import asyncio
import contextlib
import time
from pathlib import Path
import uuid
from typing import Awaitable, Callable, Optional

import aiohttp
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
import httpx
from starlette.responses import Response  # only for typing/help
from watchfiles import awatch
from schorle.registry import registry

# Helper type hints for injected callables
EnsureHttp = Callable[[str], Awaitable["httpx.AsyncClient"]]  # lazy import-safe hint
RenderFunc = Callable[..., Awaitable[Response]]
GetWsSession = Callable[[], aiohttp.ClientSession]


class DevExtension:
    """
    Development-only routes and behavior:
      - Webpack HMR WS proxy: /_next/webpack-hmr
      - Asset proxy helpers for Next dev: /_next/* and friends
      - Live dev-indicator socket: /_schorle/dev-indicator
    Consumes three helpers from Schorle:
      - ensure_http(label) -> AsyncClient
      - render(path, ...) -> StreamingResponse
      - get_ws_session() -> aiohttp.ClientSession bound to UDS connector
    """

    def __init__(
        self,
        *,
        project_root: str,
        upstream_host: str,
        upstream_ws_path: str = "/_next/webpack-hmr",
        mount_assets_proxy: bool = True,
        ensure_http: EnsureHttp,
        render: RenderFunc,
        get_ws_session: GetWsSession,
    ):
        self.project_root = Path(project_root)
        self.upstream_host = upstream_host
        self.upstream_ws_path = upstream_ws_path
        self.mount_assets_proxy = mount_assets_proxy

        self._ensure_http = ensure_http
        self._render = render
        self._get_ws_session = get_ws_session

        # Dev-indicator state
        self._dev_indicator_id = str(uuid.uuid4())
        self._start_time = time.time()

        # Public router to be included by Schorle
        self.router = APIRouter()
        self._wire_routes()
        self._wire_dev_indicator()

        self.watcher_task: Optional[asyncio.Task] = None
        self._watch_debounce_ms = 100
        self._watch_stop_event = asyncio.Event()

    def start_watcher(self):
        print("[DevExtension] Starting watcher")
        self.watcher_task = asyncio.create_task(self._watch_app_and_rerun_registry())

    def stop_watcher(self):
        print("[DevExtension] Stopping watcher")
        self._watch_stop_event.set()

        if self.watcher_task:
            self.watcher_task.cancel()
            self.watcher_task = None

    # ---------- wiring ----------

    def _wire_routes(self):
        # HMR WS passthrough
        @self.router.websocket("/_next/webpack-hmr")
        async def hmr(ws: WebSocket):
            sub = _pick_subprotocol(ws.headers.get("sec-websocket-protocol"))
            await ws.accept(subprotocol=sub)

            headers = {
                "Host": self.upstream_host,
                "Origin": ws.headers.get("origin", f"http://{self.upstream_host}:8000"),
            }
            if "cookie" in ws.headers:
                headers["Cookie"] = ws.headers["cookie"]
            protocols = [sub] if sub else None

            session = self._get_ws_session()
            try:
                upstream = await session.ws_connect(
                    f"ws://{self.upstream_host}{self.upstream_ws_path}",
                    headers=headers,
                    protocols=protocols,
                    autoping=True,
                    heartbeat=30.0,
                    compress=0,
                )

                async def c2u():
                    try:
                        while True:
                            msg = await ws.receive()
                            if "text" in msg:
                                await upstream.send_str(msg["text"])
                            elif "bytes" in msg:
                                await upstream.send_bytes(msg["bytes"])
                            elif msg.get("type") in ("websocket.disconnect", "close"):
                                await upstream.close()
                                break
                    except WebSocketDisconnect:
                        with contextlib.suppress(Exception):
                            await upstream.close()

                async def u2c():
                    try:
                        async for msg in upstream:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                await ws.send_text(msg.data)
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                await ws.send_bytes(msg.data)
                            else:
                                break
                    finally:
                        with contextlib.suppress(Exception):
                            await ws.close()

                done, pending = await asyncio.wait(
                    [asyncio.create_task(c2u()), asyncio.create_task(u2c())],
                    return_when=asyncio.FIRST_EXCEPTION,
                )
                for t in pending:
                    t.cancel()
            except Exception:
                with contextlib.suppress(Exception):
                    await ws.close(code=1011)
                raise

        # Optional: small asset proxy for dev so you don't hand-write routes.
        if self.mount_assets_proxy:
            assets = APIRouter()

            @assets.api_route(
                "/__nextjs_restart_dev",
                methods=["GET", "HEAD", "OPTIONS", "POST"],
                include_in_schema=False,
            )
            async def _restart_dev(request: Request):
                return await self._render(
                    "/__nextjs_restart_dev", method=request.method
                )

            @assets.api_route(
                "/__nextjs_server_status",
                methods=["GET", "HEAD", "OPTIONS", "POST"],
                include_in_schema=False,
            )
            async def _server_status(request: Request):
                return await self._render(
                    "/__nextjs_server_status", method=request.method
                )

            @assets.api_route(
                "/_next/{rest:path}",
                methods=["GET", "HEAD", "OPTIONS", "POST"],
                include_in_schema=False,
            )
            async def _next_assets(request: Request, rest: str):
                # stream static asset through UDS (cache headers preserved)
                return await self._render("/_next/" + rest, method=request.method)

            @assets.api_route(
                "/__nextjs_original-stack_frame",
                methods=["GET", "HEAD", "OPTIONS"],
                include_in_schema=False,
            )
            async def _dev_stack(request: Request):
                return await self._render("/__nextjs_original-stack_frame")

            @assets.api_route(
                "/__nextjs_source-map",
                methods=["GET", "HEAD", "OPTIONS"],
                include_in_schema=False,
            )
            async def _next_source_map(request: Request):
                return await self._render(
                    "/__nextjs_source-map",
                    method=request.method,
                    query_string=str(request.query_params),
                )

            self.router.include_router(assets)

    def _wire_dev_indicator(self):
        # adds a websocket route that closes when server is restarted
        @self.router.websocket("/_schorle/dev-indicator")
        async def dev_indicator(ws: WebSocket):
            await self._ensure_http("dev-indicator")
            await ws.accept()

            async def indicator():
                while True:
                    try:
                        await asyncio.sleep(1)
                        await ws.send_json(
                            {
                                "id": self._dev_indicator_id,
                                "start_time": self._start_time,
                            }
                        )
                    except Exception:
                        break

            await indicator()

    async def _watch_app_and_rerun_registry(self):
        app_dir = (self.project_root / "app").resolve()
        if not app_dir.exists():
            print(f"[DevExtension] Watch skipped: {app_dir} does not exist")
            return

        print(f"[DevExtension] Watching for changes in: {app_dir}")
        # awatch yields sets of (Change, path) tuples; debounce coalesces bursts
        async for _changes in awatch(
            app_dir,
            stop_event=self._watch_stop_event,
            debounce=self._watch_debounce_ms,
        ):
            # You can inspect `_changes` if you want to filter by ext, etc.
            try:
                print("[DevExtension] Change detected in /app — rebuilding registry…")
                registry(
                    pages=self.project_root / "app" / "pages",
                    ts_out=self.project_root / ".schorle" / "app" / "registry.gen.tsx",
                    py_out=self.project_root / "registry.py",
                    import_prefix="@/pages",
                )
                print("[DevExtension] Registry rebuild complete.")
            except Exception as e:
                print(f"[DevExtension] Registry rebuild failed: {e}")


# ---------- helpers ----------


def _pick_subprotocol(header: Optional[str]) -> Optional[str]:
    if not header:
        return None
    return header.split(",")[0].strip()
