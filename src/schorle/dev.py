import asyncio
from contextlib import asynccontextmanager
from typing import Callable
from fastapi import WebSocket
from watchfiles import awatch
from pathlib import Path
import time
import re


def schorle_filter(change, path: str) -> bool:
    """
    Custom filter function for schorle file watching.
    Returns True if the file should be watched, False if it should be ignored.
    """
    # Convert Path to string if needed
    if hasattr(path, "as_posix"):
        path_str = path.as_posix()
    else:
        path_str = str(path)

    # Ignore patterns
    ignore_patterns = [
        # Standard directories
        r".*/(\.git|\.schorle|node_modules|__pycache__|\.pytest_cache|\.mypy_cache)(/.*)?$",
        # Generated API files
        r".*/lib/api\.ts$",  # lib/api.ts at any level
        r".*\.schorle/.*",  # anything inside .schorle directory
        # Build artifacts
        r".*/dist/.*",
        r".*\.pyc$",
        r".*\.pyo$",
        r".*\.swp$",
        r".*\.tmp$",
        # Lock files
        r".*/package-lock\.json$",
        r".*/yarn\.lock$",
        r".*/bun\.lock$",
    ]

    for pattern in ignore_patterns:
        if re.match(pattern, path_str):
            return False

    print(f"[DEBUG] Watching file: {path_str}")
    return True


class DevManager:
    def __init__(
        self, root_path: Path, reload_callbacks: list[Callable[[], None]] | None = None
    ) -> None:
        self.root_path = root_path
        self._reload_callbacks: list[Callable[[], None]] = reload_callbacks or []
        self._websockets: set[WebSocket] = set()
        self._watcher_task: asyncio.Task | None = None

    def add_reload_callback(self, callback: Callable[[], None]) -> None:
        self._reload_callbacks.append(callback)

    async def websocket_endpoint(self, ws: WebSocket) -> None:
        await ws.accept()
        self._websockets.add(ws)
        try:
            while True:
                await asyncio.sleep(1)
                await ws.send_json({"start_time": time.time()})
        except Exception:
            # Connection closed or send failed; fall through to cleanup
            pass
        finally:
            if ws in self._websockets:
                self._websockets.remove(ws)

    async def _broadcast_json(self, payload: dict) -> None:
        if not self._websockets:
            return
        stale: list[WebSocket] = []
        send_tasks: list[asyncio.Task] = []
        for ws in list(self._websockets):

            async def _send(w: WebSocket) -> None:
                try:
                    await w.send_json(payload)
                except Exception:
                    stale.append(w)

            send_tasks.append(asyncio.create_task(_send(ws)))
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
        # prune any sockets that errored
        for ws in stale:
            if ws in self._websockets:
                self._websockets.remove(ws)

    async def _disconnect_all(self) -> None:
        if not self._websockets:
            return
        sockets = list(self._websockets)
        self._websockets.clear()
        await asyncio.gather(
            *(self._safe_close(ws) for ws in sockets), return_exceptions=True
        )

    async def _safe_close(self, ws: WebSocket) -> None:
        try:
            await ws.close()
        except Exception:
            pass

    async def _watcher(self) -> None:
        async for changes in awatch(self.root_path, watch_filter=schorle_filter):
            print(f"[DEBUG] File changes detected: {changes}")
            for cb in list(self._reload_callbacks):
                try:
                    cb()
                except Exception as e:
                    # Keep watcher alive even if a callback throws
                    print(f"Error in reload callback: {e}")
                    continue
            # After reload callbacks complete, notify connected dev clients to reload
            await self._broadcast_json({"type": "reload", "ts": time.time()})

    @asynccontextmanager
    async def lifespan(self, app):
        for cb in list(self._reload_callbacks):
            cb()
        try:
            self._watcher_task = asyncio.create_task(self._watcher())
            yield
        finally:
            if self._watcher_task is not None:
                self._watcher_task.cancel()
