import asyncio
from contextlib import asynccontextmanager
from typing import Callable, Optional, Sequence, Union
from fastapi import WebSocket
from watchfiles import awatch
from pathlib import Path
import time
from watchfiles.filters import DefaultFilter


class SchorleFilter(DefaultFilter):
    """
    A filter for schorle-related folders, since this class inherits from [`DefaultFilter`][watchfiles.DefaultFilter]
    folders like .schorle, node_modules, __pycache__ are ignored
    """

    def __init__(
        self,
        *,
        ignore_paths: Optional[Sequence[Union[str, Path]]] = None,
    ) -> None:
        self.ignore_dirs = list(DefaultFilter.ignore_dirs) + [
            ".schorle",
            "node_modules",
            "__pycache__",
        ]
        super().__init__(ignore_paths=ignore_paths)
        self.ignore_entity_patterns = list(DefaultFilter.ignore_entity_patterns) + [
            r"^\.schorle$",
            r"^node_modules$",
            r"^__pycache__$",
        ]


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
        async for _ in awatch(self.root_path, watch_filter=SchorleFilter()):
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
