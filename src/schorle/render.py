import json
import subprocess
from pathlib import Path
from typing import IO, Generator

from schorle.utils import SchorleProject


def _compute_page_imports(
    project: SchorleProject, page_output_dir: Path
) -> tuple[str, list[str]]:
    """Compute the module import paths for page and layouts.

    - project pages live under `<project_path>/pages`
    - `page_output_dir` is `.schorle/dist/entry/pages/{...}/{PageName}`
    """
    if not project.pages_path.exists():
        raise FileNotFoundError(f"Missing pages directory: {project.pages_path}")

    # Build relative path parts like ["dashboard", "profile", "Profile"]
    rel_from_pages = page_output_dir.relative_to(project.dist_path / "entry" / "pages")
    parts = list(rel_from_pages.parts)

    # Compute absolute file URL for page import like
    # "file:///.../pages/dashboard/profile/Profile.tsx"
    page_rel_str = "/".join(parts) + ".tsx"
    page_import = (project.pages_path / page_rel_str).resolve().as_uri()

    # Layouts: include root and each ancestor directory if `__layout.tsx` exists
    layout_imports: list[str] = []

    # Root layout
    root_layout = project.pages_path / "__layout.tsx"
    if root_layout.exists():
        layout_imports.append(root_layout.resolve().as_uri())

    # Ancestor layouts
    # For parts ["dashboard", "profile", "Profile"], ancestors are:
    # "dashboard", "dashboard/profile"
    if len(parts) > 1:
        for i in range(len(parts) - 1):
            ancestor = "/".join(parts[: i + 1])
            layout_path = project.pages_path / ancestor / "__layout.tsx"
            if layout_path.exists():
                layout_imports.append(layout_path.resolve().as_uri())

    return page_import, layout_imports


def _find_asset(dir_path: Path, suffix: str) -> Path:
    matches = sorted(p for p in dir_path.glob(f"*.{suffix.lstrip('.')}") if p.is_file())
    if not matches:
        raise FileNotFoundError(f"No *.{suffix} asset found in {dir_path}")
    return matches[0]


def render(project: SchorleProject, page_path: Path) -> Generator[bytes, None, None]:
    """Render a built page by inspecting `.schorle/dist/entry/pages`.

    page_path is something like `pages/Index.tsx` or `pages/dashboard/profile/Profile.tsx`

    - Scans for page output directories (containing both a .js and .css)
    - Derives page and layout import paths from `pages/`
    - Executes `bun run slx-ipc render <json>` in the project directory
    - Returns the stdout string from the render command
    """

    entry_pages_dir = project.dist_path / "entry" / "pages"

    # Map a source page path under `pages/` to its built output directory under
    # `.schorle/dist/entry/pages/.../{PageName}`.
    #
    # Examples:
    #   pages/Index.tsx                      -> .schorle/.../pages/Index
    #   pages/dashboard/profile/Profile.tsx  -> .schorle/.../pages/dashboard/profile/Profile
    if page_path.is_absolute():
        try:
            rel_to_project = page_path.relative_to(project.project_root)
        except ValueError:
            raise ValueError(
                f"page_path {page_path!s} must be inside project {project.project_root!s}"
            )
    else:
        rel_to_project = page_path

    # Strip leading `pages/` if present
    if rel_to_project.parts and rel_to_project.parts[0] == "pages":
        rel_from_pages = Path(*rel_to_project.parts[1:])
    else:
        rel_from_pages = rel_to_project

    # Drop the extension to get the output directory name
    page_dir = entry_pages_dir / rel_from_pages.with_suffix("")

    # Find js and css assets
    js_asset = _find_asset(page_dir, ".js")
    css_asset = _find_asset(page_dir, ".css")

    # Compute import paths
    page_import, layout_imports = _compute_page_imports(project, page_dir)

    # Prepare render info JSON
    render_info = {
        "page": page_import,
        "layouts": layout_imports,
        "js": f"/.schorle/{js_asset.relative_to(project.dist_path)}",
        # Included for completeness; the current renderer ignores css
        "css": f"/.schorle/{css_asset.relative_to(project.dist_path)}",
    }

    print(f"Render info: {render_info}")

    # Execute bun command and capture output in stream
    full_cmd = [
        "bun",
        "run",
        "slx-ipc",
        "render",
        json.dumps(render_info),
    ]

    print(f"Full command: {' '.join(full_cmd)}")
    completed = subprocess.Popen(
        full_cmd,
        cwd=str(project.root_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # if completed.returncode != 0:
    #     raise RuntimeError(f"Failed to render: {completed.stderr}")

    if completed.stdout is None:
        raise RuntimeError("Failed to render: stdout is None")

    # transform stream by decoding it and injecting CSS before </head>
    def injector(stream: IO[bytes]) -> Generator[bytes, None, None]:
        for line in stream:
            decoded = line.decode("utf-8")
            if render_info["css"]:
                link_tag = f"<link rel='stylesheet' href='{render_info['css']}' />\n"
            else:
                link_tag = ""
            injected = decoded.replace("</head>", f"{link_tag}</head>")
            yield injected.encode("utf-8")

    return injector(completed.stdout)
