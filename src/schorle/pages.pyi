# Auto-generated Python stub file for Schorle pages
# This file provides type checking for ui.pages.* access

from typing import TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from schorle.manifest import SchorleProject

class PageReference:
    """Represents a reference to a specific page file."""
    def __init__(self, page_path: Path, project: SchorleProject) -> None: ...
    @property
    def page_path(self) -> Path: ...
    @property
    def project(self) -> SchorleProject: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...

# Export functions for external use
def create_pages_accessor(project: SchorleProject) -> PagesAccessor: ...
def generate_python_stubs(
    project: SchorleProject, output_path: Path | None = None
) -> Path: ...

class PagesAccessor:
    def __init__(
        self, project: SchorleProject, path_prefix: Path | None = None
    ) -> None: ...
    @property
    def Index(self) -> PageReference: ...
