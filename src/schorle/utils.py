import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Generator
import importlib.resources

templates_path: Path = importlib.resources.files("schorle").joinpath("templates")  # type: ignore


@contextlib.contextmanager
def cwd(path: Path | str) -> Generator[None, None, None]:
    current_dir = os.getcwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(current_dir)


def define_if_dev():
    # we assume it's a dev run in following cases:
    # startup command is uvicorn with --reload flag
    # startup command contains fastapi dev

    return "--reload" in sys.argv or "fastapi dev" in sys.argv


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
