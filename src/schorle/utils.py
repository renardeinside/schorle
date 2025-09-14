import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Generator
from schorle.manifest import SchorleProject
from tomlkit import parse


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


# searches the directories upwards until it finds a pyproject.toml file
def find_schorle_project(
    path: Path, max_iterations: int = 10, left_iterations: int = 0
) -> SchorleProject:
    path = path.resolve()
    if max_iterations == 0 or left_iterations == max_iterations - 1:
        raise FileNotFoundError(
            f"pyproject.toml not found after {left_iterations} iterations"
        )
    if path.joinpath("pyproject.toml").exists():
        ## check if [tool.schorle] exists
        doc = parse(path.joinpath("pyproject.toml").read_text())
        if "tool" in doc and "schorle" in doc["tool"]:  # type: ignore
            project_root = Path(doc["tool"]["schorle"]["project_root"])  # type: ignore
            return SchorleProject(
                root_path=path,
                project_root=project_root,
            )
        else:
            return find_schorle_project(
                path.parent, max_iterations, left_iterations + 1
            )
    else:
        print(f"pyproject.toml not found in {path}, searching in {path.parent}")
        return find_schorle_project(path.parent, max_iterations, left_iterations + 1)
