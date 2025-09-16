"""
Pages module for Schorle.

This module provides the public API for page discovery and access.
The actual implementation is in page_system.py to avoid conflicts with pages.pyi.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from schorle.manifest import SchorleProject

# Import classes from the implementation module
from schorle.page_system import (
    PageReference,
    PagesAccessor,
    PythonStubGenerator,
)


# Function wrappers for proper exports
def create_pages_accessor(project: "SchorleProject") -> PagesAccessor:
    """Create a pages accessor for the given project."""
    from schorle.page_system import create_pages_accessor as _create_pages_accessor

    return _create_pages_accessor(project)


def generate_python_stubs(
    project: "SchorleProject", output_path: "Path | None" = None
) -> "Path":
    """Generate Python stub files for pages in the given project."""
    from schorle.page_system import generate_python_stubs as _generate_python_stubs

    return _generate_python_stubs(project, output_path)


__all__ = [
    "PageReference",
    "PagesAccessor",
    "PythonStubGenerator",
    "create_pages_accessor",
    "generate_python_stubs",
]
