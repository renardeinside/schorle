import base64
import json
import os
import subprocess
from pathlib import Path
from typing import IO, Generator, Union

from schorle.utils import SchorleProject
from schorle.manifest import PageInfo


def _compute_import_uris(
    project: SchorleProject, page_info: PageInfo
) -> tuple[str, list[str]]:
    """Compute file:// import URIs for page and layouts based on PageInfo."""
    if not project.pages_path.exists():
        raise FileNotFoundError(f"Missing pages directory: {project.pages_path}")

    page_import = page_info.page.resolve().as_uri()
    layout_imports = [layout.resolve().as_uri() for layout in page_info.layouts]
    return page_import, layout_imports


def _resolve_page_info(project: SchorleProject, page: Path) -> PageInfo:
    """Resolve a `Path` to a `PageInfo` by scanning the prepared manifest mapping."""
    page_infos = project.collect_page_infos()

    if page.is_absolute():
        try:
            rel_to_project = page.relative_to(project.project_root)
        except ValueError:
            rel_to_project = page
    else:
        rel_to_project = page

    # If not prefixed with pages/, assume it is relative to pages/
    if rel_to_project.parts and rel_to_project.parts[0] == "pages":
        candidate = Path(*rel_to_project.parts[1:])
    else:
        candidate = rel_to_project

    for info in page_infos:
        rel = info.page.relative_to(project.pages_path)
        if rel.with_suffix("") == candidate.with_suffix(""):
            return info

    raise FileNotFoundError(f"Page not found: {page}")


def render(
    project: SchorleProject,
    page_or_info: Union[Path, PageInfo],
    props: bytes | None = None,
) -> Generator[bytes, None, None]:
    """Render a built page using precomputed PageInfo (with js/css URLs).

    Accepts either a `PageInfo` or a `Path` for backward compatibility.
    """

    page_info = (
        page_or_info
        if isinstance(page_or_info, PageInfo)
        else _resolve_page_info(project, page_or_info)
    )

    # Compute import paths
    page_import, layout_imports = _compute_import_uris(project, page_info)

    # Prepare render info JSON
    render_info = {
        "page": page_import,
        "layouts": layout_imports,
        "js": page_info.js or "",
        # Included for completeness; the current renderer ignores css
        "css": page_info.css or "",
    }

    # Execute bun command and capture output in stream
    full_cmd = [
        "bun",
        "run",
        "slx-ipc",
        "render",
        json.dumps(render_info),
    ]

    base_env = os.environ.copy()
    base_env["NODE_ENV"] = "development" if project.dev else "production"

    completed = subprocess.Popen(
        full_cmd,
        cwd=str(project.root_path),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=base_env,
    )

    if completed.stdout is None:
        raise RuntimeError("Failed to render: stdout is None")

    # Stream props (if provided) into the bun process via stdin
    if completed.stdin is None:
        raise RuntimeError("Failed to render: stdin is None")

    if props is not None:
        try:
            completed.stdin.write(props)
            completed.stdin.flush()
        finally:
            completed.stdin.close()
    else:
        completed.stdin.close()

    # transform stream by decoding it and injecting CSS before </head>
    def injector(stream: IO[bytes]) -> Generator[bytes, None, None]:
        for line in stream:
            decoded = line.decode("utf-8")
            injection = ""

            if render_info["css"]:
                injection += f"<link rel='stylesheet' href='{render_info['css']}' />\n"

            if props:
                props_b64 = base64.b64encode(props).decode("utf-8")
                injection += f"<script id='__SCHORLE_PROPS__' type='application/msgpack'>{props_b64}</script>\n"

            injected = decoded.replace("</head>", f"{injection}</head>")
            yield injected.encode("utf-8")

    return injector(completed.stdout)
