import asyncio
import contextlib
import os
import random
import signal
import time
from pathlib import Path
from typing import AsyncIterator, Optional, Sequence, Mapping
import base64
import json
import uuid
import aiohttp
from fastapi.concurrency import asynccontextmanager
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from starlette.responses import StreamingResponse


class Schorle:
    """
    Self-contained supervisor + UDS HTTP/WS client + tiny router for HMR.
    Works with ANY FastAPI app via ui.mount(app).
    """

    def __init__(
        self,
        project_root: str | os.PathLike,
        *,
        cwd: str | os.PathLike = ".schorle",
        bun_cmd: Sequence[str] = ("bun", "run", "server.ts"),
        socket_path: str = "/tmp/bun-nextjs.sock",
        upstream_host: str = "localhost",
        base_http: str = "http://localhost",  # ignored by UDS transport
        upstream_ws_path: str = "/_next/webpack-hmr",
        ready_check_url: str = "/",
        ready_timeout_s: float = 30.0,
        retry_base_delay_s: float = 1.5,
        retry_max_delay_s: float = 30.0,
        mount_assets_proxy: bool = True,  # proxy a few Next asset paths
    ):
        self.project_root = Path(project_root)
        self.cwd = Path(cwd)
        self.bun_cmd = tuple(bun_cmd)
        self.socket_path = socket_path
        self.upstream_host = upstream_host
        self.base_http = base_http
        self.upstream_ws = f"ws://{upstream_host}{upstream_ws_path}"
        self.ready_check_url = f"{base_http}{ready_check_url}"
        self.ready_timeout_s = ready_timeout_s
        self.retry_base_delay_s = retry_base_delay_s
        self.retry_max_delay_s = retry_max_delay_s
        self.mount_assets_proxy = mount_assets_proxy

        self._http: Optional[httpx.AsyncClient] = None
        self._ws: Optional[aiohttp.ClientSession] = None
        self._shutdown_event: Optional[asyncio.Event] = None
        self._supervisor_task: Optional[asyncio.Task] = None
        self._bun_proc: Optional[asyncio.subprocess.Process] = None
        self._bun_log_tasks: tuple[asyncio.Task, asyncio.Task] | tuple[()] = ()
        self._dev_indicator_task: Optional[asyncio.Task] = None

        self._dev_indicator_id = str(uuid.uuid4())
        self._start_time = time.time()
        self._server_ready = False

        # mini-router: only HMR WS and (opt) a few asset paths for dev
        self.router = APIRouter()
        self._wire_routes()
        self._wire_dev_indicator()

    # ---------- public API ----------

    def mount(self, app):
        """
        Attach routes and compose our lifespan with the app's existing lifespan (if any).
        This avoids deprecated .add_event_handler and won't override existing handlers.
        """
        # Avoid double-mounting
        if getattr(app.state, "_schorle_lifespan_installed", False):
            print(
                "[schorle] mount() called again — skipping lifespan wiring (already installed)."
            )
        else:
            existing = getattr(app.router, "lifespan_context", None)
            print(f"[schorle] Existing lifespan detected: {bool(existing)}")

            @asynccontextmanager
            async def combined(app_):
                # Case A: existing lifespan exists -> run it AND ours.
                if existing:
                    print("[schorle] Entering combined lifespan: existing -> schorle")
                    async with existing(app_):
                        async with self._lifespan_cm(app_):
                            yield
                    print("[schorle] Exited combined lifespan: schorle -> existing")
                else:
                    # Case B: no lifespan on the app — just ours.
                    print("[schorle] Entering schorle lifespan (no existing lifespan).")
                    async with self._lifespan_cm(app_):
                        yield
                    print("[schorle] Exited schorle lifespan.")

            # Install the composed lifespan
            app.router.lifespan_context = combined  # Starlette/FastAPI-approved way
            app.state._schorle_lifespan_installed = True
            print("[schorle] Lifespan composed and installed.")

        # Routes can be included repeatedly (Starlette dedupes by path+method),
        # but we still guard to reduce noise.
        if not getattr(app.state, "_schorle_routes_mounted", False):
            app.include_router(self.router)
            app.state._schorle_routes_mounted = True
            print("[schorle] Router mounted (HMR WS and optional asset proxy).")
        else:
            print("[schorle] Router already mounted — skipping.")

    @contextlib.asynccontextmanager
    async def _lifespan_cm(self, app):
        """
        Our internal lifespan: brings up Bun supervisor + UDS clients on enter,
        tears them down on exit.
        """
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
        props: Optional[dict] = None,  # ⬅️ NEW
    ) -> StreamingResponse:
        if not route_path.startswith("/"):
            route_path = "/" + route_path

        client = await self._ensure_http()
        url = f"{self.base_http}{route_path}"
        if query_string:
            url += f"?{query_string}"

        in_headers = dict(headers or {})
        in_headers.setdefault("host", self.upstream_host)

        # ⬇️ NEW: attach props as base64-JSON header (safe for binary/UTF-8)
        if props is not None:
            raw = json.dumps(props, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
            in_headers["x-schorle-props"] = base64.b64encode(raw).decode("ascii")

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
        # Clients
        self._http = httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(uds=self.socket_path),
            timeout=None,
            http2=False,
        )
        self._ws = aiohttp.ClientSession(
            connector=aiohttp.UnixConnector(path=self.socket_path)
        )

        # Supervisor
        self._shutdown_event = asyncio.Event()
        self._supervisor_task = asyncio.create_task(self._bun_supervisor())

    async def _on_shutdown(self):
        # Stop supervisor
        if self._shutdown_event:
            self._shutdown_event.set()
        if self._supervisor_task:
            with contextlib.suppress(Exception):
                await self._supervisor_task

        # Kill bun if still around
        if self._bun_proc is not None:
            await self._terminate_proc(self._bun_proc)

        # Cancel log tasks
        for t in self._bun_log_tasks:
            with contextlib.suppress(Exception):
                t.cancel()
        self._bun_log_tasks = ()

        # Close clients
        if self._http:
            await self._http.aclose()
        if self._ws:
            await self._ws.close()
        self._http = None
        self._ws = None

    # ---------- routing ----------

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

            assert self._ws is not None, "WS client not initialized"
            try:
                upstream = await self._ws.ws_connect(
                    self.upstream_ws,
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
            async def _server_status(request: Request):
                return await self.render("/__nextjs_restart_dev", method=request.method)

            @assets.api_route(
                "/__nextjs_server_status",
                methods=["GET", "HEAD", "OPTIONS", "POST"],
                include_in_schema=False,
            )
            async def _server_status(request: Request):
                return await self.render(
                    "/__nextjs_server_status", method=request.method
                )

            @assets.api_route(
                "/_next/{rest:path}",
                methods=["GET", "HEAD", "OPTIONS", "POST"],
                include_in_schema=False,
            )
            async def _next_assets(request: Request, rest: str):
                # stream static asset through UDS (cache headers preserved)
                return await self.render("/_next/" + rest, method=request.method)

            @assets.api_route(
                "/__nextjs_original-stack_frame",
                methods=["GET", "HEAD", "OPTIONS"],
                include_in_schema=False,
            )
            async def _dev_stack(request: Request):
                return await self.render("/__nextjs_original-stack_frame")

            self.router.include_router(assets)

    # ---------- internals: HTTP/WS + supervisor ----------

    async def _ensure_http(self) -> httpx.AsyncClient:
        while not self._server_ready:
            print("⏳ Waiting for server to be ready...")
            await asyncio.sleep(0.1)
        assert self._http is not None, "HTTP client not initialized"
        return self._http

    async def _bun_supervisor(self):
        assert self._shutdown_event is not None
        shutdown_event = self._shutdown_event

        attempt = 0
        last_start = 0.0

        # reset state slots
        self._bun_proc = None
        self._bun_log_tasks = ()

        while not shutdown_event.is_set():
            attempt += 1
            start_delay = min(
                self.retry_base_delay_s * (2 ** (attempt - 1)), self.retry_max_delay_s
            )
            start_delay *= 0.85 + random.random() * 0.3

            since = time.monotonic() - last_start
            if since < 1.0:
                await asyncio.sleep(start_delay)

            print(
                f"⏳ Starting Bun server (attempt {attempt}) -> {' '.join(self.bun_cmd)}"
            )
            last_start = time.monotonic()
            try:
                proc, t_out, t_err = await self._spawn_bun()
                self._bun_proc = proc
                self._bun_log_tasks = (t_out, t_err)

                self._server_ready = await self._wait_for_ready()
                if self._server_ready:
                    print("✅ Bun server is ready (UDS reachable).")
                    attempt = 0
                else:
                    print("⚠️  Bun readiness timed out; it may still come up shortly.")

                done, pending = await asyncio.wait(
                    {
                        asyncio.create_task(proc.wait()),
                        asyncio.create_task(shutdown_event.wait()),
                    },
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if shutdown_event.is_set():
                    print("🛑 Stopping Bun (app shutdown).")
                    await self._terminate_proc(proc)
                    break

                rc = proc.returncode
                print(f"💥 Bun exited with code {rc}; scheduling restart.")

                # cleanup
                for t in self._bun_log_tasks:
                    t.cancel()
                self._bun_proc = None
                self._bun_log_tasks = ()
                for t in pending:
                    t.cancel()

            except Exception as e:
                print(f"❌ Failed to start Bun: {e!r}")
                await asyncio.sleep(start_delay)

    async def _spawn_bun(self):
        with contextlib.suppress(FileNotFoundError):
            os.unlink(self.socket_path)

        proc = await asyncio.create_subprocess_exec(
            *self.bun_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
            cwd=str(self.cwd),
        )
        t_out = asyncio.create_task(self._stream_output("🔵 [bun]", proc.stdout))  # type: ignore[arg-type]
        t_err = asyncio.create_task(self._stream_output("🔴 [bun]", proc.stderr))  # type: ignore[arg-type]
        return proc, t_out, t_err

    async def _terminate_proc(
        self, proc: asyncio.subprocess.Process, grace: float = 5.0
    ):
        try:
            if proc.pid:
                os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            await asyncio.wait_for(proc.wait(), timeout=grace)
        except asyncio.TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                if proc.pid:
                    os.killpg(proc.pid, signal.SIGKILL)

    async def _wait_for_ready(self) -> bool:
        deadline = time.monotonic() + self.ready_timeout_s

        # 1) wait for UDS to exist
        while time.monotonic() < deadline:
            if os.path.exists(self.socket_path):
                break
            await asyncio.sleep(0.05)
        else:
            return False

        # 2) probe HTTP via UDS
        async with httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(uds=self.socket_path),
            timeout=2.5,
            http2=False,
        ) as probe:
            while time.monotonic() < deadline:
                try:
                    r = await probe.get(self.ready_check_url)
                    if r.status_code < 500:
                        return True
                except Exception:
                    pass
                await asyncio.sleep(0.15)
        return False

    async def _stream_output(self, prefix: str, stream: asyncio.StreamReader):
        while True:
            line = await stream.readline()
            if not line:
                break
            print(f"{prefix} {line.decode(errors='replace').rstrip()}")

    def _wire_dev_indicator(self):
        # adds a websocket route that closes when server is restarted
        @self.router.websocket("/_schorle/dev-indicator")
        async def dev_indicator(ws: WebSocket):
            await self._ensure_http()
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


# ---------- helpers ----------


def _pick_subprotocol(header: Optional[str]) -> Optional[str]:
    if not header:
        return None
    return header.split(",")[0].strip()
