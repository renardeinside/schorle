from schorle.render import render
from schorle.utils import cwd, find_schorle_project
from pathlib import Path


def test_render():
    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))
        gen = render(proj, Path("Index.tsx"))
        for line in gen:
            print(line.decode("utf-8"))
