import json
import os
from pathlib import Path
import subprocess
import shutil
import jinja2
import importlib.resources
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from schorle.manifest import (
    PageInfo,
    BuildManifest,
    BuildManifestEntry,
    BuildManifestAssets,
    SchorleProject,
)

console = Console()


def print_build_info(message: str, style: str = "blue") -> None:
    """Print build information with consistent styling."""
    info_text = Text()
    info_text.append("● ", style="blue bold")
    info_text.append(message, style=style)
    console.print(info_text)


def print_build_error(error_message: str, details: str | None = None) -> None:
    """Print build errors in a clean, formatted way."""
    error_text = Text()
    error_text.append("✗ ", style="red bold")
    error_text.append("Build failed: ", style="red bold")
    error_text.append(error_message, style="red")
    console.print(error_text)

    if details:
        # Create a panel for error details
        console.print(
            Panel(
                details.strip(),
                title="[red]Error Details[/red]",
                border_style="red",
                padding=(1, 2),
            )
        )


def print_build_output(stdout: str, stderr: str) -> None:
    """Print build output in a clean, formatted way."""
    if stdout.strip():
        console.print(
            Panel(
                stdout.strip(),
                title="[green]Build Output[/green]",
                border_style="green",
                padding=(1, 2),
            )
        )

    if stderr.strip():
        # Filter out JSON artifacts from stderr for cleaner display
        stderr_lines = []
        for line in stderr.strip().split("\n"):
            line = line.strip()
            # Skip lines that look like JSON artifacts
            if not (line.startswith("[") or line.startswith("{")):
                stderr_lines.append(line)

        if stderr_lines:
            console.print(
                Panel(
                    "\n".join(stderr_lines),
                    title="[yellow]Build Messages[/yellow]",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )


client_template_path: Path = (
    importlib.resources.files("schorle") / "templates" / "client-entry.tsx.jinja"  # type: ignore
)

server_template_path: Path = (
    importlib.resources.files("schorle") / "templates" / "server-entry.tsx.jinja"  # type: ignore
)


def get_client_template() -> jinja2.Template:
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(client_template_path.parent))
    ).get_template(client_template_path.name)
    return template


def get_server_template() -> jinja2.Template:
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(server_template_path.parent))
    ).get_template(server_template_path.name)
    return template


# Legacy function for backward compatibility
def get_template() -> jinja2.Template:
    return get_client_template()


def transform_artifacts_to_manifest(
    artifacts: list[dict], page_infos: list[PageInfo], project: SchorleProject
) -> list[BuildManifestEntry]:
    """
    Transform build artifacts into the new manifest format.

    Maps build artifacts back to their corresponding pages and layouts.
    """
    manifest_entries = []

    # Separate client and server artifacts
    client_artifacts = [
        a for a in artifacts if a.get("target") == "client" or "target" not in a
    ]
    server_artifacts = [a for a in artifacts if a.get("target") == "server"]

    # Group client artifacts by their source entry directory
    client_entry_artifacts: dict[str, list[dict]] = {}
    for artifact in client_artifacts:
        artifact_path = artifact["path"]
        # Find which entry this artifact belongs to by checking the directory structure
        # Artifacts are organized under pages/[name]/ structure
        if artifact_path.startswith("pages/"):
            # Extract the entry key (e.g., "pages/Index" from "pages/Index/dev.js")
            path_parts = Path(artifact_path).parts
            if len(path_parts) >= 2:  # pages/[name]/file
                entry_key = "/".join(path_parts[:2])  # pages/name
                if entry_key not in client_entry_artifacts:
                    client_entry_artifacts[entry_key] = []
                client_entry_artifacts[entry_key].append(artifact)

    # Group server artifacts by their source entry directory
    server_entry_artifacts: dict[str, list[dict]] = {}
    for artifact in server_artifacts:
        artifact_path = artifact["path"]
        # Server artifacts have the same structure under pages/[name]/
        if artifact_path.startswith("pages/"):
            # Extract the entry key (e.g., "pages/Index" from "pages/Index/dev.js")
            path_parts = Path(artifact_path).parts
            if len(path_parts) >= 2:  # pages/[name]/file
                entry_key = "/".join(path_parts[:2])  # pages/name
                if entry_key not in server_entry_artifacts:
                    server_entry_artifacts[entry_key] = []
                server_entry_artifacts[entry_key].append(artifact)

    # Create manifest entries for each page
    for page_info in page_infos:
        # Find the corresponding entry key
        relative_page_path = page_info.page.relative_to(project.pages_path)
        entry_key = f"pages/{relative_page_path.with_suffix('')}"

        client_artifacts_for_page = client_entry_artifacts.get(entry_key, [])
        server_artifacts_for_page = server_entry_artifacts.get(entry_key, [])

        # Find client JS and CSS assets
        js_asset = None
        css_asset = None

        for artifact in client_artifacts_for_page:
            if artifact["kind"] in ["entry", "entry-point"] and artifact[
                "path"
            ].endswith(".js"):
                js_asset = f"/.schorle/dist/client/{artifact['path']}"
            elif artifact["path"].endswith(".css"):
                css_asset = f"/.schorle/dist/client/{artifact['path']}"

        # Find server JS asset
        server_js_asset = None
        for artifact in server_artifacts_for_page:
            if artifact["kind"] in ["entry", "entry-point"] and artifact[
                "path"
            ].endswith(".js"):
                server_js_asset = f"/.schorle/dist/server/{artifact['path']}"

        # Skip pages without client JS assets (shouldn't happen in normal builds)
        if not js_asset:
            print_build_info(
                f"Warning: No client JS asset found for page {page_info.page}",
                style="yellow",
            )
            continue

        # Create the manifest entry
        page_path = (
            page_info.page.stem
        )  # Just the filename without extension (e.g., "Index")
        layout_paths = [
            str(layout.relative_to(project.project_root))
            for layout in page_info.layouts
        ]

        assets = BuildManifestAssets(
            js=js_asset, css=css_asset, server_js=server_js_asset
        )
        entry = BuildManifestEntry(page=page_path, layouts=layout_paths, assets=assets)
        manifest_entries.append(entry)

    return manifest_entries


def build_entrypoints(command: tuple[str, ...], project: SchorleProject):
    # Discover pages and layouts using the manifest-aware API. At build time, js/css
    # might be missing; we only need the TSX imports to generate hydrator entrypoints.
    # For entrypoint generation, we do not require a manifest yet.
    page_infos: list[PageInfo] = (
        project.collect_page_infos(require_manifest=False) or []
    )

    # cleanup .schorle dir
    if project.schorle_dir.exists():
        shutil.rmtree(project.schorle_dir)
    project.schorle_dir.mkdir(parents=True, exist_ok=True)

    client_entrypoints = []
    server_entrypoints = []
    client_template = get_client_template()
    server_template = get_server_template()

    # generate .schorle files
    for page_info in page_infos:
        # put the generated file in .schorle with same relative path
        # But for MDX files, change the extension to .tsx for proper bundling
        relative_page_path = page_info.page.relative_to(project.pages_path)
        if relative_page_path.suffix == ".mdx":
            relative_page_path = relative_page_path.with_suffix(".tsx")

        # Generate import statements and layout components (shared between client and server)
        import_statements = []
        # For MDX files, keep the .mdx extension in the import path
        page_import_path = page_info.page.relative_to(project.project_root)
        if page_import_path.suffix == ".mdx":
            import_statements.append(f"import Page from '@/{page_import_path}';")
        else:
            import_statements.append(
                f"import Page from '@/{page_import_path.with_suffix('')}';"
            )

        for i, layout in enumerate(page_info.layouts):
            import_statements.append(
                f"import Layout{i + 1} from '@/{layout.relative_to(project.project_root).with_suffix('')}';"
            )
        import_statements_str = "\n".join(import_statements)

        # populate the const layouts = {{ layout_components }};
        layout_components_str = (
            "["
            + ", ".join(f"Layout{i + 1}" for i in range(len(page_info.layouts)))
            + "]"
        )

        # Generate client entry
        client_dir = project.schorle_dir / ".gen" / "client"
        client_dir.mkdir(parents=True, exist_ok=True)
        client_output_path = client_dir / relative_page_path
        client_output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(client_output_path, "w") as f:
            f.write(
                client_template.render(
                    import_statements=import_statements_str,
                    layout_components=layout_components_str,
                )
            )
        client_entrypoints.append(client_output_path)

        # Generate server entry
        server_dir = project.schorle_dir / ".gen" / "server"
        server_dir.mkdir(parents=True, exist_ok=True)
        server_output_path = server_dir / relative_page_path
        server_output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(server_output_path, "w") as f:
            f.write(
                server_template.render(
                    import_statements=import_statements_str,
                    layout_components=layout_components_str,
                )
            )
        server_entrypoints.append(server_output_path)

    # Create build config with both client and server entrypoints
    build_config = {
        "client": [str(p) for p in client_entrypoints],
        "server": [str(p) for p in server_entrypoints],
    }

    base_env = os.environ.copy()
    base_env["NODE_ENV"] = "development" if project.dev else "production"
    result = subprocess.run(
        [
            *command,
            json.dumps(build_config),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=base_env,
        text=True,
    )

    if result.returncode != 0:
        print_build_error("Bun build process failed", result.stderr)
        raise RuntimeError("Failed to build")

    # Parse the JSON artifacts from stdout or stderr
    artifacts = None

    # Try stdout first
    if result.stdout.strip():
        try:
            artifacts = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            print_build_info(
                "Could not parse JSON from stdout, trying stderr...", style="yellow"
            )

    # Fallback to stderr if stdout failed or was empty
    if artifacts is None and result.stderr.strip():
        try:
            # Sometimes the JSON might be mixed with other stderr output
            # Try to find a line that looks like JSON (starts with [ or {)
            for line in result.stderr.strip().split("\n"):
                line = line.strip()
                if line.startswith("[") or line.startswith("{"):
                    artifacts = json.loads(line)
                    break
        except json.JSONDecodeError:
            pass

    if artifacts is None:
        print_build_error(
            "Failed to parse build artifacts JSON from stdout or stderr",
            f"stdout: {result.stdout}\nstderr: {result.stderr}",
        )
        raise RuntimeError("Failed to parse build artifacts JSON from stdout or stderr")

    # Transform artifacts into the new manifest format
    manifest_entries = transform_artifacts_to_manifest(artifacts, page_infos, project)

    # Create the manifest and write it
    manifest = BuildManifest(
        entries=manifest_entries, mode="development" if project.dev else "production"
    )
    manifest_path = project.manifest_path
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w") as f:
        f.write(manifest.model_dump_json(indent=2))
