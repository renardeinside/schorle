# schorle/socket_store.py
import asyncio
import contextlib
from pathlib import Path
from schorle.settings import UdsSettings, TcpSettings


class SocketStore:
    def __init__(self, connection_config: UdsSettings | TcpSettings):
        """Initialize SocketStore with either new ConnectionConfig or legacy path"""
        self.config = connection_config
        self._store: dict[str, bytes] = {}
        self._server: asyncio.AbstractServer | None = None

    def set(self, key: str, value: bytes) -> None:
        self._store[key] = value

    async def start(self) -> None:
        if isinstance(self.config, UdsSettings):
            print(
                f"🔵 [schorle][store] Starting UDS server on {self.config.store_socket_path}"
            )
            # UDS mode
            socket_path = Path(self.config.store_socket_path)
            if socket_path.exists():
                socket_path.unlink()
            socket_path.parent.mkdir(parents=True, exist_ok=True)
            self._server = await asyncio.start_unix_server(
                self._handle_client, path=str(socket_path)
            )
            print(
                f"🔵 [schorle][store] UDS server started on {self.config.store_socket_path}"
            )
        elif isinstance(self.config, TcpSettings):
            # TCP mode
            print(
                f"🔵 [schorle][store] Starting TCP server on {self.config.host}:{self.config.store_port}"
            )
            self._server = await asyncio.start_server(
                self._handle_client, host=self.config.host, port=self.config.store_port
            )
            print(
                f"🔵 [schorle][store] TCP server started on {self.config.host}:{self.config.store_port}"
            )
        else:
            raise ValueError(f"Unsupported connection config: {type(self.config)}")

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        # Only clean up socket file for UDS connections
        if isinstance(self.config, UdsSettings):
            with contextlib.suppress(FileNotFoundError):
                socket_path = Path(self.config.store_socket_path)
                if socket_path.exists():
                    socket_path.unlink()

    def get_connection_info(self) -> dict:
        """Get connection information for clients"""
        if isinstance(self.config, UdsSettings):
            return {"mode": "uds", "socket_path": self.config.store_socket_path}
        elif isinstance(self.config, TcpSettings):
            return {
                "mode": "tcp",
                "host": self.config.host,
                "port": self.config.store_port,
            }
        else:
            raise ValueError(f"Unsupported connection config: {type(self.config)}")

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
