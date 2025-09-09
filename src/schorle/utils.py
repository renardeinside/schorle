import asyncio
import contextlib
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from typing import Any, Callable, Mapping
import json
from fastapi.datastructures import Headers
from typing_extensions import Iterable


def to_camel_case(s: str) -> str:
    """Convert snake_case, kebab-case, or spaced string to camelCase."""
    parts = re.split(r"[_\-\s]+", s)
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])


def keys_to_camel_case(
    obj: dict[str, Any] | list[Any] | Any,
) -> dict[str, Any] | list[Any] | Any:
    """Recursively convert all dict keys to camelCase."""
    if isinstance(obj, dict):
        return {
            to_camel_case(k) if isinstance(k, str) else k: keys_to_camel_case(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [keys_to_camel_case(item) for item in obj]
    else:
        return obj


def schema_to_ts(json_schema_str: str, bun_executable: Path) -> str:
    # Ensure draft is explicit (helps some tools)
    try:
        obj = json.loads(json_schema_str)
    except json.JSONDecodeError:
        obj = None
    if isinstance(obj, dict) and "$schema" not in obj:
        obj["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        json_schema_str = json.dumps(obj)

    cmd = [
        str(bun_executable),
        "x",
        "json-schema-to-typescript",
        "--unreachableDefinitions",  # emit all $defs even if not referenced
        "--format=false",  # (optional) skip prettier for speed
    ]
    proc = subprocess.run(
        cmd,
        input=json_schema_str,  # pass stdin directly
        text=True,  # let subprocess handle encoding/decoding
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return proc.stdout


def define_if_dev():
    # we assume it's a dev run in following cases:
    # startup command is uvicorn with --reload flag
    # startup command contains fastapi dev

    return "--reload" in sys.argv or "fastapi dev" in sys.argv


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


def prefer_http() -> bool:
    return os.name == "nt"


async def lines_printer_task(getter: Callable[[], list[str]], label: str):
    while True:
        lines = getter()
        if lines:
            for line in lines:
                print(f"[schorle] {label}:", line)
        await asyncio.sleep(0.1)


@contextlib.asynccontextmanager
async def lines_printer(getter: Callable[[], list[str]], label: str):
    task = asyncio.create_task(lines_printer_task(getter, label))
    try:
        yield
    except asyncio.CancelledError:
        pass
    finally:
        task.cancel()


def forwardable_headers(
    h: Headers | Mapping[str, str],
    allow: Iterable[str] = ("cookie", "user-agent", "sec-websocket-protocol"),
) -> dict[str, str]:
    allow = {k.lower() for k in allow}
    return {k: v for k, v in dict(h).items() if k.lower() in allow and v is not None}


def find_project_root() -> Path | None:
    current_dir = Path.cwd()
    for root, dirs, files in os.walk(current_dir):
        if ".schorle" in dirs:
            return Path(root)
    return None
