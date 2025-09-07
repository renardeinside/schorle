# schorle/socket_store.py
import asyncio
import contextlib
import os
from pathlib import Path


class SocketStore:
    """
    Minimal in-memory KV store with a tiny UDS server.
    Protocol: client sends a single line:  GET /{key}\n
    Server replies with the value (or empty string) + '\n', then closes.
    """

    def __init__(self, socket_path: str | os.PathLike):
        self.socket_path = Path(socket_path)
        self._store: dict[str, str] = {}
        self._server: asyncio.AbstractServer | None = None

    # --- KV API ---
    def set(self, key: str, value: str) -> None:
        self._store[key] = value

    # --- Server lifecycle ---
    async def start(self) -> None:
        # Make sure old socket file isn’t in the way
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[store] Starting server on {self.socket_path}")

        # Use the UNIX-domain variant explicitly
        self._server = await asyncio.start_unix_server(
            self._handle_client,
            path=str(self.socket_path),
        )
        print(f"[store] Server started on {self.socket_path}")

    async def stop(self) -> None:
        print(f"[store] Stopping server on {self.socket_path}")
        if self._server is None:
            # Best-effort cleanup even if start() never completed
            with contextlib.suppress(FileNotFoundError):
                if self.socket_path.exists():
                    self.socket_path.unlink()
            return

        self._server.close()
        await self._server.wait_closed()
        self._server = None

        # Clean up the socket file
        with contextlib.suppress(FileNotFoundError):
            if self.socket_path.exists():
                self.socket_path.unlink()
        print(f"[store] Server stopped on {self.socket_path}, socket file removed")

    # --- Connection handler ---
    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            line = await reader.readline()  # read until '\n'
            req = line.decode("utf-8", errors="replace").strip()

            # Expect: GET /key
            method, _, path = (req + "  ").partition(" ")

            if method.lower() != "get":
                print(f"[store] Unsupported method: {method}")
                resp = "\n"
            else:
                key = path.lstrip().lstrip("/").rstrip()

                if key not in self._store:
                    raise KeyError(f"Key not found: {key}")
                value = self._store[key]
                resp = value + "\n"
                del self._store[key]

            writer.write(resp.encode("utf-8"))
            await writer.drain()
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
