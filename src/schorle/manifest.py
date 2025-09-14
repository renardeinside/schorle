from __future__ import annotations
from pydantic import BaseModel
from pathlib import Path
import json


class SchorleProject(BaseModel):
    root_path: Path
    project_root: Path
    dev: bool | None = None

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
    def raw_manifest_path(self) -> Path:
        return self.dist_path / "entry" / "manifest.json"

    @property
    def raw_manifest(self) -> list[RawManifestEntry]:
        # The manifest is a JSON array written by the Bun build step
        # e.g. [{ kind, path, loader, bytes }, ...]

        try:
            text = self.raw_manifest_path.read_text()
        except FileNotFoundError:
            return []
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        return [RawManifestEntry.model_validate(item) for item in data]

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

        # Build a lookup from entry directory (e.g. "pages/Index" or
        # "pages/dashboard/Profile") to its js and css assets using the manifest
        manifest_entries = self._build_manifest_lookup() if require_manifest else {}

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
                entry_dir_key = str(Path("pages") / relative_path.with_suffix(""))
                assets = manifest_entries.get(entry_dir_key)
                if assets is None:
                    # Skip pages that have no corresponding built assets yet
                    # (e.g., build not run). Caller can handle empty list accordingly.
                    continue

                js_url, css_url = assets

                page_layout_pairs.append(
                    PageInfo(page=tsx_file, layouts=layouts, js=js_url, css=css_url)
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

    def _build_manifest_lookup(self) -> dict[str, tuple[str, str | None]]:
        """
        Build a lookup of entry directory -> (js_url, css_url) from the raw manifest.

        - Entry directory example keys:
          "pages/Index", "pages/dashboard/Profile"
        - js_url/css_url are public URLs under "/.schorle/" that the server exposes.
        """
        entries = self.raw_manifest

        # First, collect JS entry directories
        js_dirs: dict[str, str] = {}
        for item in entries:
            path_str = str(item.path)
            if not path_str.endswith(".js"):
                continue
            kind = (item.kind or "").lower()
            if kind not in {"entry", "entry-point"}:
                continue
            directory = str(Path(path_str).parent)
            js_dirs[directory] = f"/.schorle/dist/entry/{path_str}"

        # Then, associate CSS assets to the closest JS directory prefix
        dir_to_css: dict[str, str] = {}
        for item in entries:
            path_str = str(item.path)
            if not path_str.endswith(".css"):
                continue
            css_dir = str(Path(path_str).parent)

            # Find the longest js_dir that is a prefix of css_dir
            best_match: str | None = None
            for js_dir in js_dirs.keys():
                if css_dir == js_dir or css_dir.startswith(js_dir + "/"):
                    if best_match is None or len(js_dir) > len(best_match):
                        best_match = js_dir
            if best_match is not None:
                dir_to_css[best_match] = f"/.schorle/dist/entry/{path_str}"

        # Build final lookup for only the keys under pages/*
        lookup: dict[str, tuple[str, str | None]] = {}
        for directory, js_url in js_dirs.items():
            if not directory.startswith("pages/"):
                continue
            css_url = dir_to_css.get(directory)
            lookup[directory] = (js_url, css_url)

        return lookup


class RawManifestEntry(BaseModel):
    kind: str
    path: Path
    loader: str | None = None
    bytes: int


class ManifestEntry(BaseModel):
    js: str
    css: str | None = None
    layouts: list[str]


class Manifest(BaseModel):
    entries: dict[str, ManifestEntry]


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
