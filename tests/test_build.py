from pathlib import Path
from schorle.build import build_entrypoints
from schorle.utils import cwd


def test_build_entrypoints():
    with cwd("packages/aurora/src/aurora/ui"):
        build_entrypoints(("bun", "run", "slx-ipc", "build"), Path("pages"), Path("."))
