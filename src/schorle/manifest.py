from __future__ import annotations
from pydantic import BaseModel
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class SchorleProject(BaseModel):
    root_path: Path
    project_root: Path
    dev: bool | None = None
    _page_infos: list[PageInfo] | None = None

    @property
    def schorle_dir(self) -> Path:
        return self.root_path / ".schorle"

    @property
    def pages_path(self) -> Path:
        return self.project_root / "pages"

    @property
    def dist_path(self) -> Path:
        return self.schorle_dir / "dist"

    @property
    def manifest_path(self) -> Path:
        return self.dist_path / "manifest.json"

    @property
    def manifest(self) -> BuildManifest:
        """Read the manifest file fresh every time to avoid caching issues."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {self.manifest_path}")

        # Always read the file fresh to ensure we get the latest content
        manifest_content = self.manifest_path.read_text()
        manifest = BuildManifest.model_validate_json(manifest_content)

        # Debug logging to track manifest reads and content
        if logger.isEnabledFor(logging.DEBUG):
            asset_info = []
            for entry in manifest.entries:
                asset_info.append(
                    f"{entry.page}: js={entry.assets.js}, css={entry.assets.css}"
                )
            logger.debug(
                f"Read manifest from {self.manifest_path} - entries: {asset_info}"
            )

        return manifest

    def collect_page_infos(self, require_manifest: bool = True) -> list[PageInfo]:
        """
        Collect all page files and their associated layout files.

        The search logic mirrors the build process:
        - Consider every "**/*.tsx" file under `pages_path` as a potential page
          except files starting with "__" (which are treated as layout or infra files).
        - For each page, include the root layout ("__layout.tsx") if present and any
          nested directory "__layout.tsx" files up the path tree.

        Returns a list of pairs: (page_path, [layout_paths...])
        """
        tsx_files = list(self.pages_path.glob("**/*.tsx"))

        # Build a lookup from page name to assets using the new manifest
        manifest_lookup: dict[str, BuildManifestAssets] = {}
        if require_manifest:
            try:
                # Always read the manifest fresh to avoid caching issues
                manifest = self.manifest
                for entry in manifest.entries:
                    manifest_lookup[entry.page] = entry.assets
            except (FileNotFoundError, json.JSONDecodeError):
                # Manifest doesn't exist or is invalid, continue without assets
                pass

        page_layout_pairs: list[PageInfo] = []
        for tsx_file in tsx_files:
            if tsx_file.name.startswith("__"):
                continue

            relative_path = tsx_file.relative_to(self.pages_path)
            parts = list(relative_path.parts[:-1])

            # always include root layout if exists by marking root with "/"
            parts = ["/"] + parts

            layouts: list[Path] = []
            for part in parts:
                if part == "/":
                    layout_path = self.pages_path.joinpath("__layout.tsx")
                else:
                    layout_path = self.pages_path.joinpath(part, "__layout.tsx")
                if layout_path.exists():
                    layouts.append(layout_path)

            if require_manifest:
                # Look up assets by page name (e.g., "Index" for "Index.tsx")
                page_name = relative_path.stem
                assets = manifest_lookup.get(page_name)
                if assets is None:
                    # Skip pages that have no corresponding built assets yet
                    # (e.g., build not run). Caller can handle empty list accordingly.
                    continue

                page_layout_pairs.append(
                    PageInfo(
                        page=tsx_file, layouts=layouts, js=assets.js, css=assets.css
                    )
                )
            else:
                # During the entrypoint generation phase, we may not have a manifest yet.
                # Still collect pages and layouts so we can generate hydrator files.
                page_layout_pairs.append(
                    PageInfo(page=tsx_file, layouts=layouts, js=None, css=None)
                )

        return page_layout_pairs

    @property
    def page_infos(self) -> list[PageInfo]:
        # Dynamically compute on each access to reflect latest files and manifest
        return self.collect_page_infos(require_manifest=True)

    def get_manifest_entry(self, page_name: str) -> BuildManifestEntry | None:
        """Get a manifest entry by page name (e.g., 'Index').

        Always reads the manifest fresh to avoid caching issues between dev/prod modes.
        """
        try:
            # Always read the manifest fresh to ensure we get the latest content
            manifest = self.manifest
            for entry in manifest.entries:
                if entry.page == page_name:
                    return entry
            return None
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def find_page_file(self, page_name: str) -> Path | None:
        """Find the actual page file by page name."""
        potential_files = [
            self.pages_path / f"{page_name}.tsx",
            self.pages_path / page_name / "index.tsx",
        ]
        for file_path in potential_files:
            if file_path.exists():
                return file_path
        return None

    def get_page_layouts(self, page_file: Path) -> list[Path]:
        """Get layouts for a specific page file."""
        relative_path = page_file.relative_to(self.pages_path)
        parts = list(relative_path.parts[:-1])

        # always include root layout if exists by marking root with "/"
        parts = ["/"] + parts

        layouts: list[Path] = []
        for part in parts:
            if part == "/":
                layout_path = self.pages_path.joinpath("__layout.tsx")
            else:
                layout_path = self.pages_path.joinpath(part, "__layout.tsx")
            if layout_path.exists():
                layouts.append(layout_path)

        return layouts

    def _invalidate_page_cache(self):
        """Invalidate cached page info to force fresh reads from the manifest."""
        self._page_infos = None

    def resolve_page_info(self, page: Path) -> PageInfo:
        """Resolve a page path to its PageInfo, including assets and layouts."""
        if self._page_infos is None:
            self._page_infos = self.collect_page_infos()

        # Normalize to project-relative pages path
        if page.is_absolute():
            try:
                rel_to_project = page.relative_to(self.project_root)
            except ValueError:
                rel_to_project = page
        else:
            rel_to_project = page

        # If not prefixed with pages/, assume it is relative to pages/
        if rel_to_project.parts and rel_to_project.parts[0] == "pages":
            candidate = Path(*rel_to_project.parts[1:])
        else:
            candidate = rel_to_project

        # Match by filepath under pages (case-sensitive) ignoring extension
        for info in self._page_infos or []:
            rel = info.page.relative_to(self.pages_path)
            if rel.with_suffix("") == candidate.with_suffix(""):
                return info

        raise FileNotFoundError(f"Page not found: {page}")


class PageInfo(BaseModel):
    page: Path
    layouts: list[Path]
    js: str | None = None
    css: str | None = None

    def __str__(self):
        layout_str = " -> ".join(
            str(layout.relative_to(self.page.parent.parent)) for layout in self.layouts
        )
        return (
            f"{self.page.relative_to(self.page.parent.parent)} (Layouts: {layout_str})"
        )


class BuildManifestAssets(BaseModel):
    js: str
    css: str | None = None


class BuildManifestEntry(BaseModel):
    page: str
    layouts: list[str]
    assets: BuildManifestAssets


class BuildManifest(BaseModel):
    entries: list[BuildManifestEntry]
