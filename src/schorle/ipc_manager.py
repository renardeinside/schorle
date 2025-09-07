# --- ipc_manager.py (new IpcManager) ---

import asyncio
import contextlib
import os
import random
import signal
import time
from typing import Optional

import httpx

from schorle.settings import IpcSettings, TcpSettings, UdsSettings


class IpcManager:
    """
    Supervises a Bun process that exposes an HTTP/WS server over a Unix domain socket.
    Responsibilities:
      - create/own socket path
      - start/stop the Bun child process with exponential backoff
      - readiness probe over UDS (file existence + HTTP GET)
      - stream child stdout/stderr
    """

    def __init__(self, *, ipc: IpcSettings):
        self.cfg: IpcSettings = ipc

        # Runtime state
        self._shutdown_event: Optional[asyncio.Event] = None
        self._supervisor_task: Optional[asyncio.Task] = None
        self._bun_proc: Optional[asyncio.subprocess.Process] = None
        self._bun_log_tasks: tuple[asyncio.Task, asyncio.Task] | tuple[()] = ()
        self._server_ready: bool = False

    @property
    def is_ready(self) -> bool:
        return self._server_ready

    async def start(self) -> None:
        if self._supervisor_task is not None:
            return
        self._shutdown_event = asyncio.Event()
        self._supervisor_task = asyncio.create_task(self._supervisor_loop())

    async def wait_until_ready(self) -> None:
        # actively poll readiness flag
        deadline = time.monotonic() + self.cfg.ready_timeout_s
        while time.monotonic() < deadline:
            if self._server_ready:
                return
            await asyncio.sleep(0.05)
        # one last probe (in case it flipped but flag not updated)
        self._server_ready = await self._wait_for_ready()

    async def stop(self) -> None:
        # signal supervisor to exit
        if self._shutdown_event:
            self._shutdown_event.set()
        if self._supervisor_task:
            with contextlib.suppress(Exception):
                await self._supervisor_task
        self._supervisor_task = None
        self._shutdown_event = None

        # Kill bun if still around
        if self._bun_proc is not None:
            await self._terminate_proc(self._bun_proc)
        self._bun_proc = None

        # Cancel log tasks
        for t in self._bun_log_tasks:
            with contextlib.suppress(Exception):
                t.cancel()
        self._bun_log_tasks = ()

    # --------- internals: supervisor ---------

    async def _supervisor_loop(self):
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
                self.cfg.retry_base_delay_s * (2 ** (attempt - 1)),
                self.cfg.retry_max_delay_s,
            )
            start_delay *= 0.85 + random.random() * 0.3

            since = time.monotonic() - last_start
            if since < 1.0:
                await asyncio.sleep(start_delay)

            print(
                f"⏳ Starting Bun server (attempt {attempt}) -> {' '.join(map(str, self.cfg.server_cmd))} in dir {self.cfg.command_dir}"
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

    async def _spawn_bun(
        self,
    ) -> tuple[asyncio.subprocess.Process, asyncio.Task | None, asyncio.Task | None]:
        if isinstance(self.cfg.transport, UdsSettings):
            with contextlib.suppress(FileNotFoundError):
                os.unlink(self.cfg.transport.socket_path)

        full_env = os.environ.copy()

        full_env.update(self.cfg.env)

        print(
            f"🔵 [bun] Starting Bun server with command: {' '.join(map(str, self.cfg.server_cmd))}"
        )
        print(f"🔵 [bun] Command directory: {self.cfg.command_dir}")

        proc = await asyncio.create_subprocess_exec(
            *map(str, self.cfg.server_cmd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
            cwd=str(self.cfg.command_dir),
            env=full_env,
        )

        if self.cfg.with_bun_logs:
            t_out = asyncio.create_task(self._stream_output("🔵 [bun]", proc.stdout))  # type: ignore[arg-type]
            t_err = asyncio.create_task(self._stream_output("🔴 [bun]", proc.stderr))  # type: ignore[arg-type]
        else:
            t_out = None
            t_err = None

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
        deadline = time.monotonic() + self.cfg.ready_timeout_s
        print(f"🔵 [bun] Waiting for ready: {deadline - time.monotonic():.2f}s")

        if isinstance(self.cfg.transport, UdsSettings):
            print(
                f"🔵 [bun] Waiting for UDS to exist: {self.cfg.transport.socket_path}"
            )
            # 1) wait for UDS to exist
            while time.monotonic() < deadline:
                if os.path.exists(self.cfg.transport.socket_path):
                    break
                await asyncio.sleep(0.05)
            else:
                return False

            print(f"🔵 [bun] UDS exists: {self.cfg.transport.socket_path}")

            # 2) probe HTTP via UDS
            async with httpx.AsyncClient(
                transport=httpx.AsyncHTTPTransport(uds=self.cfg.transport.socket_path),
                timeout=2.5,
                http2=False,
            ) as probe:
                while time.monotonic() < deadline:
                    try:
                        to_deadline = deadline - time.monotonic()
                        print(
                            f"🔵 [bun] Probing HTTP via UDS: {self.cfg.transport.socket_path} (to deadline: {to_deadline:.2f}s)"
                        )
                        r = await probe.get(
                            f"http://localhost/{self.cfg.ready_check_url}"
                        )
                        if r.status_code < 500:
                            return True
                    except Exception:
                        pass
                    await asyncio.sleep(0.15)
        elif isinstance(self.cfg.transport, TcpSettings):
            print(
                f"🔵 [bun] Waiting for TCP to be reachable: {self.cfg.transport.host}:{self.cfg.transport.port}"
            )
            # 1) probe HTTP via TCP
            async with httpx.AsyncClient(
                base_url=f"http://{self.cfg.transport.host}:{self.cfg.transport.port}",
                timeout=2.5,
                http2=False,
            ) as probe:
                while time.monotonic() < deadline:
                    try:
                        r = await probe.get(
                            f"http://{self.cfg.transport.host}:{self.cfg.transport.port}/{self.cfg.ready_check_url}"
                        )
                        if r.status_code < 500:
                            return True
                    except Exception:
                        pass
                    await asyncio.sleep(0.15)
        else:
            raise ValueError(f"Unsupported transport: {type(self.cfg.transport)}")
        return False

    async def _stream_output(self, prefix: str, stream: asyncio.StreamReader):
        while True:
            line = await stream.readline()
            if not line:
                break
            print(f"{prefix} {line.decode(errors='replace').rstrip()}")
