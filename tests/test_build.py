from pathlib import Path
from schorle.build import build_entrypoints
from schorle.utils import cwd
from schorle.manifest import find_schorle_project


def test_build_entrypoints():
    with cwd("packages/aurora"):
        proj = find_schorle_project(Path.cwd())
        build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)
        assert proj.manifest.entries[0].page == "Index"
