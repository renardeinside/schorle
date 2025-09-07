from pydantic import BaseModel, Field

import os
import sys
from pathlib import Path
import socket


def define_if_dev():
    # we assume it's a dev run in following cases:
    # os.environ.get("SCHORLE_ENV") == "development"
    # startup command is uvicorn with --reload flag
    # startup command contains fastapi dev

    return (
        os.environ.get("SCHORLE_ENV") == "development"
        or "--reload" in sys.argv
        or "fastapi dev" in sys.argv
    )


class SchorleSettings(BaseModel):
    # Schorle app/runtime config
    project_root: Path = Field(..., description="Project root directory")
    upstream_host: str = Field(
        "localhost", description="Host header & origin used for upstream dev server"
    )
    base_http: str = Field(
        "http://localhost", description="Base URL path used for UDS or HTTP requests"
    )
    upstream_ws_path: str = Field(
        "/_next/webpack-hmr", description="HMR websocket path on upstream"
    )
    dev_mode_enabled: bool = Field(
        default_factory=define_if_dev,
        description="Enable DevExtension (HMR, assets, dev-indicator)",
    )
    prefer_http: bool = Field(False, description="Prefer HTTP over UDS for IPC")


class UdsSettings(BaseModel):
    socket_path: str = Field(..., description="Explicit UDS path; random if None")
    store_socket_path: str = Field(
        ..., description="Explicit UDS path for store; random if None"
    )


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


class TcpSettings(BaseModel):
    host: str = Field(..., description="Host to connect to NextJS process")
    port: int = Field(
        default_factory=find_free_port, description="Port to connect to NextJS process"
    )

    store_host: str = Field(..., description="Host to run the store process on")
    store_port: int = Field(
        default_factory=find_free_port, description="Port to run the store process on"
    )


class IpcSettings(BaseModel):
    command_dir: Path = Field(..., description="Directory to run the command in")
    # Bun/IPC supervision config
    bun_executable: str = Field(..., description="Bun executable to use")
    transport: UdsSettings | TcpSettings = Field(..., description="IPC settings")
    ready_check_url: str = Field(
        "/schorle/render", description="Path to probe for readiness"
    )
    ready_timeout_s: float = Field(
        30.0, description="Max seconds to wait for readiness"
    )
    retry_base_delay_s: float = Field(1.5, description="Supervisor backoff base")
    retry_max_delay_s: float = Field(30.0, description="Supervisor backoff cap")
    with_bun_logs: bool = Field(False, description="Stream Bun logs to stdout")
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables to set for bun child process",
    )

    @property
    def server_cmd(self) -> tuple[str | int, ...]:
        if isinstance(self.transport, UdsSettings):
            return (
                self.bun_executable,
                "run",
                "server.ts",
                "uds",
                self.transport.socket_path,
                self.transport.store_socket_path,
            )
        elif isinstance(self.transport, TcpSettings):
            return (
                self.bun_executable,
                "run",
                "server.ts",
                "http",
                self.transport.host,
                self.transport.port,
                self.transport.store_host,
                self.transport.store_port,
            )
        else:
            raise ValueError(f"Unsupported transport: {type(self.transport)}")
