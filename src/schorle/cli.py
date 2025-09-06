import shutil
import json
import subprocess
import typer
from pathlib import Path
import importlib.metadata
import importlib.resources
import os
from schorle.registry import registry

__version__ = importlib.metadata.version("schorle")
templates_path = importlib.resources.files("schorle").joinpath("templates")


app = typer.Typer(
    name="schorle",
    help="Schorle is a framework for building powerful data-driven applications.",
)


@app.command(name="version", help="Show the version of the schorle CLI")
def version():
    typer.echo(f"Schorle version {__version__}")


@app.command(name="init", help="Initialize a new project")
def init(
    project_name: str = typer.Argument(..., help="The name of the project"),
    project_path: Path = typer.Argument(..., help="The path to the project"),
):
    typer.echo(f"Generating project {project_name} at {project_path}")

    if project_path.exists():
        shutil.rmtree(project_path)

    project_path.mkdir(parents=True, exist_ok=True)
    schorle_path = project_path / ".schorle"
    schorle_path.mkdir(parents=True, exist_ok=True)

    # run bun init in project_path
    subprocess.run(
        [
            "bun",
            "create",
            "next-app",
            "schorle",
            "--use-bun",
            "--typescript",
            "--tailwind",
            "--yes",
        ],
        cwd=project_path,
    )

    os.rename(project_path / "schorle", schorle_path)

    # put project_name into .schorle/package.json
    package_json = schorle_path / "package.json"
    content = json.loads(package_json.read_text())
    content["name"] = project_name
    package_json.write_text(json.dumps(content, indent=2))

    # copy ../templates/.schorle/tsconfig.json to schorle_path/tsconfig.json
    shutil.copy(
        templates_path / ".schorle" / "tsconfig.json",
        schorle_path / "tsconfig.json",
    )

    # prepare project_path/app/components
    (project_path / "app" / "components").mkdir(parents=True, exist_ok=True)

    # add shadcn
    subprocess.run(
        ["bunx", "--bun", "shadcn@latest", "init", "--yes", "-b", "neutral"],
        cwd=schorle_path,
    )
    # add next-themes
    subprocess.run(["bun", "add", "next-themes"], cwd=schorle_path)

    # add button
    subprocess.run(
        ["bunx", "--bun", "shadcn@latest", "add", "button"], cwd=schorle_path
    )

    # copy ../templates/server.ts to project_path/server.ts
    shutil.copy(
        templates_path / "server.ts",
        schorle_path / "server.ts",
    )

    # copy ../templates/tsconfig.json to project_path/tsconfig.json
    shutil.copy(
        templates_path / "tsconfig.json",
        project_path / "tsconfig.json",
    )

    # init uv in project_path
    subprocess.run(["uv", "init", "--no-workspace", "--app", "."], cwd=project_path)

    # install schorle python package
    schorle_package_path = importlib.resources.files("schorle").parent.parent
    subprocess.run(["uv", "add", "--editable", schorle_package_path], cwd=project_path)

    # copy pages/index.tsx to project_path/app/pages/index.tsx
    project_path.joinpath("app").joinpath("pages").mkdir(parents=True, exist_ok=True)

    shutil.copy(
        templates_path / "pages" / "Index.tsx",
        project_path / "app" / "pages" / "Index.tsx",
    )

    # copy ../templates/theme to schorle_path/components/theme
    shutil.copytree(
        templates_path / "components" / "theme",
        project_path / "app" / "components" / "theme",
    )

    # copy ../templates/layout.tsx to schorle_path/app/layout.tsx
    shutil.copy(
        templates_path / "layout.tsx",
        project_path / "app" / "pages" / "__layout.tsx",
    )

    # copy ../templates/page.tsx to schorle_path/app/[[...slug]]/page.tsx
    schorle_path.joinpath("app").joinpath("[[...slug]]").mkdir(
        parents=True, exist_ok=True
    )

    shutil.copy(
        templates_path / "page.tsx",
        schorle_path / "app" / "[[...slug]]" / "page.tsx",
    )

    # remove .schorle/app/page.tsx and .schorle/app/layout.tsx
    (schorle_path / "app" / "page.tsx").unlink()
    (schorle_path / "app" / "layout.tsx").unlink()

    # add
    # this -> @source "../../app/pages/";
    # after -> @import "tw-animate-css";
    # to file schorle_path/app/styles/globals.css
    styles_file = schorle_path / "app" / "globals.css"
    content = styles_file.read_text()
    content = content.replace(
        '@import "tw-animate-css";',
        "\n".join(
            [
                '@import "tw-animate-css";',
                '@source "../../app/pages/";',
                '@source "../../app/components/";',
            ]
        ),
    )
    styles_file.write_text(content)

    # add symlink from schorle_path/node_modules to project_path/node_modules

    (project_path / "node_modules").symlink_to(
        Path(".schorle/node_modules"), target_is_directory=True
    )

    # gen pages
    registry(
        pages=project_path / "app" / "pages",
        out=schorle_path / "app" / "registry.gen.tsx",
        import_prefix="@/pages",
    )

    # copy ./template/.schorle/layout.tsx to schorle_path/app/layout.tsx
    shutil.copy(
        templates_path / ".schorle" / "layout.tsx",
        schorle_path / "app" / "layout.tsx",
    )

    # copy ./template/app.py to project_path/app.py
    shutil.copy(
        templates_path / "app.py",
        project_path / "main.py",
    )

    # copy ./template/SchorleDevIndicator.tsx to project_path/app/components/dev/SchorleDevIndicator.tsx
    (project_path / "app" / "components" / "dev").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        templates_path / "components" / "dev" / "SchorleDevIndicator.tsx",
        project_path / "app" / "components" / "dev" / "SchorleDevIndicator.tsx",
    )

    # add uvicorn[standard]
    subprocess.run(["uv", "add", "uvicorn[standard]"], cwd=project_path)


app.command(
    name="registry",
    help="Scan a /pages tree and emit a TypeScript lazy-import registry.",
)(registry)
