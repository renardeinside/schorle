"""
Pages discovery and access system for Schorle.

Provides dynamic attribute access to pages (e.g. ui.pages.Index, ui.pages.dashboard.About)
and generates stub files for type checking.
"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Any
import logging

if TYPE_CHECKING:
    from schorle.manifest import SchorleProject

logger = logging.getLogger(__name__)


class PageReference:
    """Represents a reference to a specific page file."""

    def __init__(self, page_path: Path, project: SchorleProject):
        self.page_path = page_path
        self.project = project

    def __str__(self) -> str:
        return str(self.page_path.relative_to(self.project.pages_path))

    def __repr__(self) -> str:
        return f"PageReference({self.page_path.relative_to(self.project.pages_path)})"


class PagesAccessor:
    """
    Provides dynamic attribute access to pages using dot notation.

    Examples:
        ui.pages.Index -> points to "Index.tsx"
        ui.pages.dashboard.About -> points to "dashboard/About.tsx"
    """

    def __init__(self, project: SchorleProject, path_prefix: Path | None = None):
        self.project = project
        self.path_prefix = path_prefix or Path()
        self._cache: dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        # Use cache to avoid repeated filesystem lookups
        if name in self._cache:
            return self._cache[name]

        current_path = self.project.pages_path / self.path_prefix

        # Check if it's a direct page file
        page_file = current_path / f"{name}.tsx"
        if page_file.exists():
            page_ref = PageReference(page_file, self.project)
            self._cache[name] = page_ref
            return page_ref

        # Check if it's a directory with pages
        dir_path = current_path / name
        if dir_path.exists() and dir_path.is_dir():
            # Check if directory has any .tsx files
            tsx_files = list(dir_path.glob("*.tsx"))
            has_subdirs = any(
                p.is_dir() for p in dir_path.iterdir() if not p.name.startswith(".")
            )

            if tsx_files or has_subdirs:
                accessor = PagesAccessor(self.project, self.path_prefix / name)
                self._cache[name] = accessor
                return accessor

        raise AttributeError(f"No page or page directory found for '{name}'")

    def __dir__(self) -> list[str]:
        """Return available page names for autocompletion."""
        current_path = self.project.pages_path / self.path_prefix

        if not current_path.exists():
            return []

        names = []

        # Add page files (without .tsx extension)
        for tsx_file in current_path.glob("*.tsx"):
            if not tsx_file.name.startswith("__"):  # Skip layout files
                names.append(tsx_file.stem)

        # Add directories with pages
        for item in current_path.iterdir():
            if (
                item.is_dir()
                and not item.name.startswith(".")
                and not item.name.startswith("__")
            ):
                # Check if directory has any .tsx files or subdirectories
                has_content = any(item.glob("*.tsx")) or any(
                    p.is_dir() for p in item.iterdir() if not p.name.startswith(".")
                )
                if has_content:
                    names.append(item.name)

        return sorted(names)


class PythonStubGenerator:
    """Generates Python .pyi stub files for pages to provide type checking support."""

    def __init__(self, project: SchorleProject):
        self.project = project

    def generate_stub_content(self) -> str:
        """Generate the content of the Python stub file."""
        lines = [
            "# Auto-generated Python stub file for Schorle pages",
            "# This file provides type checking for ui.pages.* access",
            "",
            "from typing import TYPE_CHECKING",
            "from pathlib import Path",
            "",
            "if TYPE_CHECKING:",
            "    from schorle.manifest import SchorleProject",
            "",
            "class PageReference:",
            '    """Represents a reference to a specific page file."""',
            "    def __init__(self, page_path: Path, project: SchorleProject) -> None: ...",
            "    @property",
            "    def page_path(self) -> Path: ...",
            "    @property",
            "    def project(self) -> SchorleProject: ...",
            "    def __str__(self) -> str: ...",
            "    def __repr__(self) -> str: ...",
            "",
            "# Export functions for external use",
            "def create_pages_accessor(project: SchorleProject) -> PagesAccessor: ...",
            "def generate_python_stubs(project: SchorleProject, output_path: Path | None = None) -> Path: ...",
            "",
        ]

        # Build the class structure
        class_content = self._build_class_tree()
        lines.extend(class_content)

        return "\n".join(lines)

    def _build_class_tree(self) -> list[str]:
        """Build the Python class tree from the pages directory."""
        if not self.project.pages_path.exists():
            return ["class PagesAccessor:", "    pass"]

        tree = self._scan_directory(self.project.pages_path)
        return self._generate_class_from_tree("PagesAccessor", tree)

    def _scan_directory(
        self, dir_path: Path, relative_to: Path | None = None
    ) -> dict[str, Any]:
        """Scan a directory and build a tree structure."""
        if relative_to is None:
            relative_to = dir_path

        tree: dict[str, Any] = {}

        if not dir_path.exists():
            return tree

        for item in dir_path.iterdir():
            if item.name.startswith(".") or item.name.startswith("__"):
                continue

            if item.is_file() and item.suffix == ".tsx":
                # Add page file
                tree[item.stem] = "PageReference"
            elif item.is_dir():
                # Recursively scan subdirectory
                subtree = self._scan_directory(item, relative_to)
                if subtree:  # Only add if subdirectory has content
                    tree[item.name] = subtree

        return tree

    def _generate_class_from_tree(
        self, class_name: str, tree: dict[str, Any], indent: int = 0
    ) -> list[str]:
        """Generate Python class from tree structure."""
        indent_str = "    " * indent
        lines = [f"{indent_str}class {class_name}:"]

        if not tree:
            lines.append(f"{indent_str}    pass")
            return lines

        # Add constructor
        lines.append(
            f"{indent_str}    def __init__(self, project: SchorleProject, path_prefix: Path | None = None) -> None: ..."
        )
        lines.append("")

        for key, value in sorted(tree.items()):
            if isinstance(value, str):
                # It's a page reference
                lines.append(f"{indent_str}    @property")
                lines.append(f"{indent_str}    def {key}(self) -> {value}: ...")
                lines.append("")
            elif isinstance(value, dict):
                # It's a nested class
                nested_class_name = f"{class_name}_{key.capitalize()}"
                lines.append(f"{indent_str}    @property")
                lines.append(
                    f"{indent_str}    def {key}(self) -> {nested_class_name}: ..."
                )
                lines.append("")

        # Generate nested classes after the main class
        for key, value in sorted(tree.items()):
            if isinstance(value, dict):
                nested_class_name = f"{class_name}_{key.capitalize()}"
                lines.append("")
                nested_lines = self._generate_class_from_tree(
                    nested_class_name, value, indent
                )
                lines.extend(nested_lines)

        return lines

    def write_stub_file(self, output_path: Path | None = None) -> Path:
        """Write the Python stub file to disk."""
        if output_path is None:
            # Create stub file for the pages module (not page_system) for better IDE support
            pages_module_path = Path(__file__).parent / "pages.pyi"
            output_path = pages_module_path

        # Ensure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self.generate_stub_content()
        output_path.write_text(content)

        # Also write app.pyi for the Schorle class typing
        app_stub_path = Path(__file__).parent / "app.pyi"
        if not app_stub_path.exists():
            self._write_app_stub(app_stub_path)

        logger.info(f"Generated Python pages stub file: {output_path}")
        return output_path

    def _write_app_stub(self, output_path: Path) -> None:
        """Write the app.pyi stub file for Schorle class typing."""
        content = """# Auto-generated stub file for Schorle app module
# This provides type checking for ui.pages access

from typing import Union
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.datastructures import Headers
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from schorle.pages import PagesAccessor, PageReference

class Schorle:
    def __init__(self, dev: bool | None = None) -> None: ...
    
    def mount(self, app: FastAPI) -> None: ...
    
    def render(
        self,
        page: Union[Path, PageReference],
        props: dict | BaseModel | None = None,
        req: Request | None = None,
        headers: Headers | None = None,
        cookies: dict[str, str] | None = None,
    ) -> StreamingResponse: ...
    
    @property
    def pages(self) -> PagesAccessor: ...
"""
        output_path.write_text(content)


def create_pages_accessor(project: SchorleProject) -> PagesAccessor:
    """Create a pages accessor for the given project."""
    return PagesAccessor(project)


def generate_python_stubs(
    project: SchorleProject, output_path: Path | None = None
) -> Path:
    """Generate Python stub files for pages in the given project."""
    generator = PythonStubGenerator(project)
    return generator.write_stub_file(output_path)
