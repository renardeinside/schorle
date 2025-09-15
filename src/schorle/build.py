import json
import os
from pathlib import Path
import subprocess
import shutil
import jinja2
import importlib.resources

from schorle.manifest import (
    PageInfo,
    BuildManifest,
    BuildManifestEntry,
    BuildManifestAssets,
)
from schorle.utils import SchorleProject

template_path: Path = (
    importlib.resources.files("schorle") / "templates" / "entry.tsx.jinja"  # type: ignore
)


def get_template() -> jinja2.Template:
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_path.parent))
    ).get_template(template_path.name)
    return template


def transform_artifacts_to_manifest(
    artifacts: list[dict], page_infos: list[PageInfo], project: SchorleProject
) -> list[BuildManifestEntry]:
    """
    Transform build artifacts into the new manifest format.

    Maps build artifacts back to their corresponding pages and layouts.
    """
    manifest_entries = []

    # Group artifacts by their source entry directory
    entry_artifacts: dict[str, list[dict]] = {}
    for artifact in artifacts:
        artifact_path = artifact["path"]
        # Find which entry this artifact belongs to by checking the directory structure
        # Artifacts are organized under pages/[name]/ structure
        if artifact_path.startswith("pages/"):
            # Extract the entry key (e.g., "pages/Index" from "pages/Index/dev.js")
            path_parts = Path(artifact_path).parts
            if len(path_parts) >= 2:  # pages/[name]/file
                entry_key = "/".join(path_parts[:2])  # pages/name
                if entry_key not in entry_artifacts:
                    entry_artifacts[entry_key] = []
                entry_artifacts[entry_key].append(artifact)

    # Create manifest entries for each page
    for page_info in page_infos:
        # Find the corresponding entry key
        relative_page_path = page_info.page.relative_to(project.pages_path)
        entry_key = f"pages/{relative_page_path.with_suffix('')}"

        artifacts_for_page = entry_artifacts.get(entry_key, [])

        # Find JS and CSS assets
        js_asset = None
        css_asset = None

        for artifact in artifacts_for_page:
            if artifact["kind"] in ["entry", "entry-point"] and artifact[
                "path"
            ].endswith(".js"):
                js_asset = f"/.schorle/dist/entry/{artifact['path']}"
            elif artifact["path"].endswith(".css"):
                css_asset = f"/.schorle/dist/entry/{artifact['path']}"

        # Skip pages without JS assets (shouldn't happen in normal builds)
        if not js_asset:
            print(f"Warning: No JS asset found for page {page_info.page}")
            continue

        # Create the manifest entry
        page_path = (
            page_info.page.stem
        )  # Just the filename without extension (e.g., "Index")
        layout_paths = [
            str(layout.relative_to(project.project_root))
            for layout in page_info.layouts
        ]

        assets = BuildManifestAssets(js=js_asset, css=css_asset)
        entry = BuildManifestEntry(page=page_path, layouts=layout_paths, assets=assets)
        manifest_entries.append(entry)

    return manifest_entries


def build_entrypoints(command: tuple[str, ...], project: SchorleProject) -> None:
    # Discover pages and layouts using the manifest-aware API. At build time, js/css
    # might be missing; we only need the TSX imports to generate hydrator entrypoints.
    # For entrypoint generation, we do not require a manifest yet.
    page_infos: list[PageInfo] = (
        project.collect_page_infos(require_manifest=False) or []
    )

    for page_info in page_infos:
        print(f"Page: {page_info}")

    # cleanup .schorle dir
    if project.schorle_dir.exists():
        shutil.rmtree(project.schorle_dir)
    project.schorle_dir.mkdir(parents=True, exist_ok=True)

    hydrator_entrypoints = []
    template = get_template()

    # generate .schorle files
    for page_info in page_infos:
        # put the generated file in .schorle with same relative path
        relative_page_path = page_info.page.relative_to(project.pages_path)
        output_path = project.schorle_dir / ".gen" / relative_page_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Generating {output_path}")
        with open(output_path, "w") as f:
            import_statements = []
            import_statements.append(
                f"import Page from '@/{page_info.page.relative_to(project.project_root).with_suffix('')}';"
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
            f.write(
                template.render(
                    import_statements=import_statements_str,
                    layout_components=layout_components_str,
                )
            )
        hydrator_entrypoints.append(output_path)
    print("Generated all entry files.")
    print("Running bun build...")
    # run bun build on all generated files

    base_env = os.environ.copy()
    base_env["NODE_ENV"] = "development" if project.dev else "production"
    result = subprocess.run(
        [
            *command,
            json.dumps([str(p) for p in hydrator_entrypoints]),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=base_env,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Failed to build")

    print("Built all entry files.")

    # Parse the JSON artifacts from stdout or stderr
    artifacts = None

    # Try stdout first
    if result.stdout.strip():
        try:
            artifacts = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            print("Could not parse JSON from stdout, trying stderr...")

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
        print(f"Build output - stdout: {result.stdout}")
        print(f"Build output - stderr: {result.stderr}")
        raise RuntimeError("Failed to parse build artifacts JSON from stdout or stderr")

    # Transform artifacts into the new manifest format
    manifest_entries = transform_artifacts_to_manifest(artifacts, page_infos, project)

    # Create the manifest and write it
    manifest = BuildManifest(entries=manifest_entries)
    manifest_path = project.manifest_path
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w") as f:
        f.write(manifest.model_dump_json(indent=2))

    print(f"Generated manifest at {manifest_path}")
