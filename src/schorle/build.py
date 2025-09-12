import json
from pathlib import Path
import subprocess
from pydantic import BaseModel
import shutil
import jinja2
import importlib.resources

from schorle.utils import SchorleProject

template_path: Path = (
    importlib.resources.files("schorle") / "templates" / "entry.tsx.jinja"  # type: ignore
)


def get_template() -> jinja2.Template:
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_path.parent))
    ).get_template(template_path.name)
    return template


class PageInfo(BaseModel):
    page: Path
    layouts: list[Path]

    def __str__(self):
        layout_str = " -> ".join(
            str(layout.relative_to(self.page.parent.parent)) for layout in self.layouts
        )
        return (
            f"{self.page.relative_to(self.page.parent.parent)} (Layouts: {layout_str})"
        )


def build_entrypoints(command: tuple[str, ...], project: SchorleProject) -> None:
    # find all **/*.tsx files
    tsx_files = list(project.pages_path.glob("**/*.tsx"))

    # expected structure looks like:
    # /path/to/pages/Index.tsx
    # /path/to/pages/__layout.tsx
    # /path/to/pages/dashboard/__layout.tsx
    # /path/to/pages/dashboard/Settings.tsx
    # /path/to/pages/dashboard/profile/Profile.tsx

    page_infos: list[PageInfo] = []
    for tsx_file in tsx_files:
        if tsx_file.name.startswith("__"):
            continue

        relative_path = tsx_file.relative_to(project.pages_path)
        # parts will be like ('dashboard', 'profile', 'Profile.tsx') for nested files
        # and ('Index.tsx',) for top-level files
        # we need to cover both cases

        parts = list(relative_path.parts[:-1])  # exclude the file name

        # always include root layout if exists
        parts = ["/"] + parts

        layouts = []

        for part in parts:
            print(f"Checking for layout in part: {part}")

            if part == "/":
                layout_path = project.pages_path.joinpath("__layout.tsx")
            else:
                layout_path = project.pages_path.joinpath(part, "__layout.tsx")

            if layout_path.exists():
                layouts.append(layout_path)

        page_infos.append(PageInfo(page=tsx_file, layouts=layouts))

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
    result = subprocess.run(
        [
            *command,
            json.dumps([str(p) for p in hydrator_entrypoints]),
        ],
    )
    if result.returncode != 0:
        print(result.stderr)
        print(result.stdout)
        raise RuntimeError("Failed to build")
    print("Built all entry files.")
