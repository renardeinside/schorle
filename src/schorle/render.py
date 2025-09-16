import base64
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import IO, Generator, Union

from fastapi.datastructures import Headers
from pydantic import BaseModel

from schorle.manifest import SchorleProject
from schorle.manifest import PageInfo

logger = logging.getLogger(__name__)


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
    """Resolve a `Path` to a `PageInfo` by scanning the prepared manifest mapping.

    Always reads the manifest fresh to avoid caching issues between dev/prod modes.
    """
    # Always get fresh page infos to ensure we have the latest manifest data
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
    page: Union[str, Path, PageInfo],
    props: bytes | None = None,
    headers: Headers | BaseModel | None = None,
    cookies: dict[str, str] | BaseModel | None = None,
) -> Generator[bytes, None, None]:
    """Render a built page using precomputed PageInfo (with js/css URLs).

    Args:
        project: The Schorle project
        page: Page to render - can be:
            - str: Page name (e.g., "Index" for Index.tsx) - uses BuildManifest
            - Path: Path to page file - uses legacy path resolution
            - PageInfo: Pre-computed page info object
        props: Optional props to pass to the page

    Returns:
        Generator yielding rendered page bytes
    """

    # Handle different input types
    if isinstance(page, PageInfo):
        page_info = page
    elif isinstance(page, str):
        # String page name - use BuildManifest approach (preferred)
        manifest_entry = project.get_manifest_entry(page)
        if manifest_entry is None:
            raise FileNotFoundError(f"Page not found in manifest: {page}")

        # Debug logging to track what assets are being used for rendering
        logger.debug(
            f"Rendering page '{page}' with assets: js={manifest_entry.assets.js}, css={manifest_entry.assets.css}"
        )

        page_file = project.find_page_file(page)
        if page_file is None:
            raise FileNotFoundError(f"Page file not found: {page}")

        layouts = project.get_page_layouts(page_file)

        # Create a PageInfo object
        page_info = PageInfo(
            page=page_file,
            layouts=layouts,
            js=manifest_entry.assets.js,
            css=manifest_entry.assets.css,
            server_js=manifest_entry.assets.server_js,
        )
    else:
        # Path - use legacy path resolution
        page_info = _resolve_page_info(project, page)

    # Check if we have a built server JS file
    if not page_info.server_js:
        raise RuntimeError(f"No server-side build available for page: {page_info.page}")

    # Convert server_js URL to local file path
    # server_js format: "/.schorle/dist/server/pages/Index/hash.js"
    server_js_path = page_info.server_js.lstrip("/")  # Remove leading /
    server_js_file = project.root_path / server_js_path

    if not server_js_file.exists():
        raise FileNotFoundError(f"Server JS file not found: {server_js_file}")

    # convert headers and cookies to dicts
    _headers = {}
    _cookies = {}
    if headers is not None:
        if isinstance(headers, BaseModel):
            _headers = headers.model_dump()
        elif isinstance(headers, Headers):
            _headers = dict(headers)
    if cookies is not None:
        if isinstance(cookies, BaseModel):
            _cookies = cookies.model_dump()
        elif isinstance(cookies, dict):
            _cookies = cookies

    # Prepare render request for the built server module
    render_request = {
        "headers": _headers if _headers else None,
        "cookies": _cookies if _cookies else None,
        "js": page_info.js or "",
        "css": page_info.css or "",
    }

    # Execute bun command to run the built server module
    full_cmd = [
        "bun",
        "run",
        "slx-ipc",
        "render-built",
        str(server_js_file),
        json.dumps(render_request),
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

            if render_request["css"]:
                injection += (
                    f"<link rel='stylesheet' href='{render_request['css']}' />\n"
                )

            if props:
                props_b64 = base64.b64encode(props).decode("utf-8")
                injection += f"<script id='__SCHORLE_PROPS__' type='application/msgpack'>{props_b64}</script>\n"

            if render_request["headers"]:
                injection += f"<script id='__SCHORLE_HEADERS__' type='application/json'>{json.dumps(render_request['headers'])}</script>\n"

            if render_request["cookies"]:
                injection += f"<script id='__SCHORLE_COOKIES__' type='application/json'>{json.dumps(render_request['cookies'])}</script>\n"

            injected = decoded.replace("</head>", f"{injection}</head>")
            yield injected.encode("utf-8")

    return injector(completed.stdout)
