# schorle/socket_store.py
import asyncio
import contextlib
import os
from pathlib import Path


class SocketStore:
    def __init__(self, socket_path: str | os.PathLike):
        self.socket_path = Path(socket_path)
        self._store: dict[str, bytes] = {}
        self._server: asyncio.AbstractServer | None = None

    def set(self, key: str, value: bytes) -> None:
        self._store[key] = value

    async def start(self) -> None:
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        self._server = await asyncio.start_unix_server(
            self._handle_client, path=str(self.socket_path)
        )

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        with contextlib.suppress(FileNotFoundError):
            if self.socket_path.exists():
                self.socket_path.unlink()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            # ---- Read HTTP request line ----
            request_line = await reader.readline()  # e.g. b"GET /key HTTP/1.1\r\n"
            if not request_line:
                return
            try:
                method, target, _ = (
                    request_line.decode("utf-8", "replace").strip().split(" ", 2)
                )
            except ValueError:
                await self._write_http(
                    writer, 400, b"Bad Request\n", content_type=b"text/plain"
                )
                return

            # ---- Drain headers until blank line ----
            # Bun sends headers; consume them so we can respond properly.
            while True:
                line = await reader.readline()
                if not line or line in (b"\r\n", b"\n"):
                    break

            if method.upper() != "GET":
                await self._write_http(
                    writer,
                    405,
                    b"Method Not Allowed\n",
                    content_type=b"text/plain",
                    extra_headers=[(b"Allow", b"GET")],
                )
                return

            key = target.lstrip("/")

            if key not in self._store:
                await self._write_http(
                    writer, 404, b"Not Found\n", content_type=b"text/plain"
                )
                return

            body = self._store.pop(key)
            # Return msgpack bytes
            await self._write_http(
                writer, 200, body, content_type=b"application/msgpack"
            )
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def _write_http(
        self,
        writer: asyncio.StreamWriter,
        status: int,
        body: bytes,
        *,
        content_type: bytes = b"application/octet-stream",
        extra_headers: list[tuple[bytes, bytes]] | None = None,
    ) -> None:
        reason_map = {
            200: b"OK",
            400: b"Bad Request",
            404: b"Not Found",
            405: b"Method Not Allowed",
        }
        reason = reason_map.get(status, b"OK")
        headers = [
            (b"Content-Type", content_type),
            (b"Content-Length", str(len(body)).encode()),
            (b"Connection", b"close"),
        ]
        if extra_headers:
            headers.extend(extra_headers)

        writer.write(b"HTTP/1.1 " + str(status).encode() + b" " + reason + b"\r\n")
        for k, v in headers:
            writer.write(k + b": " + v + b"\r\n")
        writer.write(b"\r\n")
        if body:
            writer.write(body)
        await writer.drain()
