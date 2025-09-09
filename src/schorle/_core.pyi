# schorle.pyi
from typing import Mapping, Iterable, Any, Awaitable

class HttpResponse:
    status: int
    def headers(self) -> Mapping[str, str]: ...
    async def read(self) -> bytes: ...
    async def aiter_bytes(self) -> Iterable[bytes]: ...  # async iterator

class WebSocketConn:
    async def send_text(self, text: str) -> None: ...
    async def send_bytes(self, data: bytes) -> None: ...
    async def receive(self) -> tuple[str, str] | tuple[str, bytes] | None: ...
    async def close(self) -> None: ...

    # Async iterator support
    def __aiter__(self) -> "WebSocketConn": ...
    async def __anext__(self) -> str | bytes: ...

class FastClient:
    def __init__(self, base_url: str, socket_path: str | None = ...) -> None: ...
    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str] | None = ...,
        headers: Mapping[str, str] | None = ...,
        cookies: Mapping[str, str] | None = ...,
        body: bytes | str | None = ...,
    ) -> HttpResponse: ...
    async def request_stream(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str] | None = ...,
        headers: Mapping[str, str] | None = ...,
        cookies: Mapping[str, str] | None = ...,
        body: bytes | str | None = ...,
    ) -> HttpResponse: ...
    async def ws_connect(
        self, path: str, *, headers: Mapping[str, str] | None = ..., secure: bool = ...
    ) -> WebSocketConn: ...

class SocketStore:
    """
    A key-value store server that can operate over Unix Domain Sockets (UDS) or TCP.
    Values are removed when fetched (one-shot store).
    """
    def __init__(
        self,
        socket_path: str | None = ...,
        host: str | None = ...,
        port: int | None = ...,
    ) -> None: ...
    def set(self, key: str, value: bytes) -> None:
        """Store a value by key. Values are removed when fetched."""
        ...

    async def __aenter__(self) -> Awaitable[None]: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any | None,
    ) -> Awaitable[None]: ...
    async def start(self) -> None:
        """Start the server (TCP or UDS)."""
        ...

    async def stop(self) -> None:
        """Stop the server and clean up (including UDS socket removal)."""
        ...

    def get_connection_info(self) -> dict[str, Any]:
        """
        Get connection information.
        Returns dict with keys: mode, socket_path (for UDS) or host/port (for TCP).
        """
        ...

    def set_log_level(self, level: str) -> None:
        """Set log level: "off" | "error" | "warn" | "info" | "debug" | "trace" """
        ...

    def get_log_level(self) -> str:
        """Get current log level as string."""
        ...

class ProcessSupervisor:
    """
    A process supervisor that manages a child process with output capture.
    """
    def __init__(
        self, cmd: list[str], cwd: str | None = ..., env: dict[str, str] | None = ...
    ) -> None:
        """
        Create a process supervisor for a command.

        Args:
            cmd: argv as a list of strings, e.g. ["bun", "run", "dev"].
            cwd: optional current working directory as a string.
            env: optional environment variables as a dict[str, str].
        """
        ...

    def __aenter__(self) -> None: ...
    def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any | None,
    ) -> None: ...
    def start(self) -> None:
        """Start the process supervisor (no-op if already started)."""
        ...

    def stop(self) -> None:
        """Stop the process supervisor and wait for the child to exit."""
        ...

    def status(self) -> dict[str, Any]:
        """
        Return current status as a dict: {state, pid, exit_code, error}

        state: "idle" | "starting" | "running" | "stopping" | "exited" | "error"
        """
        ...

    @property
    def is_running(self) -> bool:
        """True iff process is in "running" state."""
        ...

    @property
    def pid(self) -> int | None:
        """Current PID or None."""
        ...

    def get_stdout_lines(self) -> list[str]:
        """Get and clear captured stdout lines since last call."""
        ...

    def get_stderr_lines(self) -> list[str]:
        """Get and clear captured stderr lines since last call."""
        ...
