"""Tests for schorle.app module."""

from pathlib import Path

from schorle.manifest import find_schorle_project


def test_schorle_init(initialized_project: Path):
    """Test Schorle initialization in dev mode."""

    proj = find_schorle_project(Path.cwd())
