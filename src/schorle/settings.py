import secrets
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from schorle.bun import check_and_prepare_bun
from schorle.utils import define_if_dev, find_free_port, prefer_http


class StoreSettings(BaseSettings):
    host: str = Field(
        default="localhost", description="Host to run the store process on"
    )
    port: int = Field(
        default_factory=find_free_port, description="Port to run the store process on"
    )
    socket_path: str = Field(
        default_factory=lambda: f"/tmp/slx-store-{secrets.token_hex(8)}.sock",
        description="Explicit UDS path; random if None",
    )


class ProxySettings(BaseSettings):
    host: str = Field(
        default="localhost", description="Host to connect to NextJS process"
    )
    port: int = Field(
        default_factory=find_free_port, description="Port to connect to NextJS process"
    )
    socket_path: str = Field(
        default_factory=lambda: f"/tmp/slx-{secrets.token_hex(8)}.sock",
        description="Explicit UDS path; random if None",
    )
    render_endpoint: str = Field(
        "/schorle/render", description="Path to probe for readiness"
    )


class SchorleSettings(BaseSettings):
    # Schorle app/runtime config

    model_config = SettingsConfigDict(env_prefix="SCHORLE_", extra="allow")

    bun_executable: Path = Field(
        default_factory=check_and_prepare_bun, description="Bun executable to use"
    )
    project_root: Path = Field(..., description="Project root directory")
    prefer_http: bool = Field(
        default_factory=prefer_http, description="Prefer HTTP over UDS for IPC"
    )
    dev: bool = Field(default_factory=define_if_dev, description="Enable dev mode")
    proxy: ProxySettings = Field(
        default_factory=ProxySettings, description="Proxy settings"
    )
    store: StoreSettings = Field(
        default_factory=StoreSettings, description="Store settings"
    )

    @property
    def schorle_dir(self) -> Path:
        return self.project_root / ".schorle"

    @property
    def proxy_cmd(self) -> list[str]:
        if self.prefer_http:
            return list(
                map(
                    str,
                    (
                        self.bun_executable,
                        "run",
                        "server.ts",
                        "http",
                        self.proxy.host,
                        self.proxy.port,
                        self.store.host,
                        self.store.port,
                    ),
                )
            )
        else:
            return list(
                map(
                    str,
                    (
                        self.bun_executable,
                        "run",
                        "server.ts",
                        "uds",
                        self.proxy.socket_path,
                        self.store.socket_path,
                    ),
                )
            )
