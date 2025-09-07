from pydantic import BaseModel, Field
from typing import Optional, Sequence
import os
import sys


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
    upstream_host: str = Field(
        "localhost", description="Host header & origin used for upstream dev server"
    )
    base_http: str = Field(
        "http://localhost", description="Base URL path used for UDS HTTP requests"
    )
    upstream_ws_path: str = Field(
        "/_next/webpack-hmr", description="HMR websocket path on upstream"
    )
    mount_assets_proxy: bool = Field(
        True, description="Proxy Next asset/dev routes during development"
    )
    enable_dev_extension: bool = Field(
        default_factory=define_if_dev,
        description="Enable DevExtension (HMR, assets, dev-indicator)",
    )


class IpcSettings(BaseModel):
    # Bun/IPC supervision config
    bun_cmd: Sequence[str] = Field(
        ("bun", "run", "server.ts"), description="Command to launch upstream dev server"
    )
    socket_path: Optional[str] = Field(
        None, description="Explicit UDS path; random if None"
    )
    store_socket_path: Optional[str] = Field(
        None, description="Explicit UDS path for store; random if None"
    )
    ready_check_url: str = Field("/pages/", description="Path to probe for readiness")
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
