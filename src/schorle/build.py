import json
import os
from pathlib import Path
import subprocess
import shutil
import jinja2
import importlib.resources

from schorle.manifest import PageInfo
from schorle.utils import SchorleProject

template_path: Path = (
    importlib.resources.files("schorle") / "templates" / "entry.tsx.jinja"  # type: ignore
)


def get_template() -> jinja2.Template:
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_path.parent))
    ).get_template(template_path.name)
    return template


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
    )
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Failed to build")

    print("Built all entry files.")
