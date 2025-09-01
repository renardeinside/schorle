import shutil
import json
import subprocess
from textwrap import dedent
import typer
from pathlib import Path
import importlib.metadata

from schorle.common import static_template_path
from schorle.generator import generate_module
from schorle.render import render as render_fn

__version__ = importlib.metadata.version("schorle")


app = typer.Typer(
    name="schorle",
    help="Schorle is a framework for building powerful data-driven applications.",
)


@app.command(name="version")
def version():
    typer.echo(f"Schorle version {__version__}")


def prepare_py_project(project_path: Path, project_name: str):
    # check if project path exists, if not, create it
    if not project_path.exists():
        project_path.mkdir(parents=True, exist_ok=True)
    # check if project path is a directory, if not, error
    if not project_path.is_dir():
        raise typer.BadParameter(f"Project path {project_path} is not a directory.")

    # run uv init in the project path
    subprocess.run(
        ["uv", "init", "--no-workspace", "--lib", "--name", project_name],
        cwd=project_path,
        check=True,
    )

    # install schorle dep
    subprocess.run(
        ["uv", "add", "/Users/renarde/projects/schorle", "--editable"],
        cwd=project_path,
        check=True,
    )
    # install fastapi and uvicorn
    subprocess.run(
        ["uv", "add", "fastapi", "uvicorn"],
        cwd=project_path,
        check=True,
    )


@app.command(name="init")
def init(
    project_name: str = typer.Argument(
        help="The name of the project.",
    ),
    project_path: Path = typer.Argument(
        default_factory=Path.cwd,
        help="The path to the project.",
    ),
):
    prepare_py_project(project_path, project_name)

    # # populate ui folder
    ui_path = project_path / "src" / project_name / "ui"
    ui_path.mkdir(parents=True, exist_ok=True)

    schorle_path = ui_path / ".schorle"
    schorle_path.mkdir(parents=True, exist_ok=True)

    app_path = ui_path / "app"
    app_path.mkdir(parents=True, exist_ok=True)

    # run bun init
    subprocess.run(
        ["bun", "init", "-y", "-m"],
        cwd=ui_path,
        check=True,
    )

    # save project_name to package.json
    package_json = ui_path / "package.json"
    package_json_payload = json.loads(package_json.read_text())
    package_json_payload["name"] = project_name
    package_json.write_text(json.dumps(package_json_payload, indent=2))

    dependencies = ["tailwindcss", "bun-plugin-tailwind", "react", "react-dom"]

    subprocess.run(
        ["bun", "add", *dependencies],
        cwd=ui_path,
        check=True,
    )

    subprocess.run(
        ["bun", "link", "schorle", "--save"],
        cwd=ui_path,
        check=True,
    )

    # update the tsconfig.json to support the ui folder
    tsconfig_json = schorle_path / "tsconfig.json"
    tsconfig_payload = {
        "compilerOptions": {
            "lib": ["ESNext", "DOM"],
            "target": "ESNext",
            "module": "Preserve",
            "moduleDetection": "force",
            "jsx": "react-jsx",
            "allowJs": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "verbatimModuleSyntax": True,
            "noEmit": True,
            "strict": True,
            "skipLibCheck": True,
            "noFallthroughCasesInSwitch": True,
            "noUncheckedIndexedAccess": True,
            "noImplicitOverride": True,
            "baseUrl": ".",
            "paths": {"@/*": ["../app/*"]},
            "noUnusedLocals": False,
            "noUnusedParameters": False,
            "noPropertyAccessFromIndexSignature": False,
        },
        "exclude": ["dist", "node_modules"],
    }

    tsconfig_json.write_text(json.dumps(tsconfig_payload, indent=2))

    tsconfig_in_ui = ui_path / "tsconfig.json"
    tsconfig_in_ui.write_text(
        json.dumps(
            {"extends": "./.schorle/tsconfig.json"},
            indent=2,
        )
    )

    # # populate ui folder with:
    # # pages/index.tsx
    # # components/ (just a folder)
    # # index.css
    app_path.joinpath("pages").mkdir(parents=True, exist_ok=True)

    shutil.copy(static_template_path / "Index.tsx", app_path / "pages" / "Index.tsx")

    # shadcn setup
    shadcn_deps = [
        "class-variance-authority",
        "clsx",
        "tailwind-merge",
        "lucide-react",
        "tw-animate-css",
        "sonner",
    ]

    subprocess.run(
        ["bun", "add", *shadcn_deps],
        cwd=ui_path,
        check=True,
    )
    styles_dir = app_path / "styles"
    styles_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(static_template_path / "globals.css", styles_dir / "globals.css")

    lib_dir = app_path / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(static_template_path / "utils.ts", lib_dir / "utils.ts")

    components_file_payload = {
        "$schema": "https://ui.shadcn.com/schema.json",
        "style": "new-york",
        "rsc": False,
        "tsx": True,
        "tailwind": {
            "config": "",
            "css": "app/styles/globals.css",
            "baseColor": "neutral",
            "cssVariables": True,
            "prefix": "",
        },
        "aliases": {
            "components": "@/components",
            "utils": "@/lib/utils",
            "ui": "@/components/ui",
            "lib": "@/lib",
            "hooks": "@/hooks",
        },
        "iconLibrary": "lucide",
    }
    components_file = ui_path / "components.json"
    components_file.write_text(json.dumps(components_file_payload, indent=2))

    # add theme components
    shutil.copytree(static_template_path / "theme", app_path / "components" / "theme")

    # add root layout
    shutil.copy(static_template_path / "__root.tsx", app_path / "pages" / "__root.tsx")

    # add schorle-level gitignore
    ui_gitignore = ui_path / ".gitignore"
    shutil.copy(static_template_path / ".ui_gitignore", ui_gitignore)

    # add button component
    subprocess.run(
        ["bunx", "shadcn@latest", "add", "button"],
        cwd=ui_path,
        check=True,
    )

    # add project-level gitignore
    root_gitignore = project_path / ".gitignore"
    shutil.copy(static_template_path / ".root_gitignore", root_gitignore)

    build(ui_path)

    # add fastapi app
    fastapi_app_file = project_path / "src" / project_name / "app.py"

    fastapi_app_file.write_text(
        dedent(f"""
        from fastapi import FastAPI
        from {project_name}.ui import Index, mount_assets

        app = FastAPI()
        mount_assets(app)
        
        @app.get("/")
        async def read_root():
            return Index.to_response()

        """).strip()
    )

    subprocess.run(
        ["git", "init"],
        cwd=project_path,
        check=True,
    )

    generate_module(ui_path, "exact")


@app.command(name="build")
def build(
    project_path: Path = typer.Argument(
        default_factory=Path.cwd,
        help="The path to the project.",
    ),
):
    if not project_path.exists():
        raise typer.BadParameter(f"Project path {project_path} does not exist.")

    source_dir_resolved = str((project_path / "app" / "pages").absolute())
    output_dir_resolved = str((project_path / ".schorle" / "dist").absolute())
    project_root_resolved = str((project_path).absolute())

    command = [
        "schorle-bridge",
        "build",
        source_dir_resolved,
        project_root_resolved,
        output_dir_resolved,
    ]

    subprocess.run(
        # args:
        # sourceDir (where the pages are)
        # projectRoot (where the project is)
        # outputDir (where the output should be)
        command,
        cwd=project_path,
        check=True,
    )


@app.command(name="render")
def render(
    project_path: Path = typer.Argument(
        default_factory=Path.cwd,
        help="The path to the project.",
    ),
    page_name: str = typer.Argument(
        help="The name of the page to render.",
    ),
):
    if not project_path.exists():
        raise typer.BadParameter(f"Project path {project_path} does not exist.")

    if not page_name:
        raise typer.BadParameter("Page name is required.")

    typer.echo(render_fn(project_path, page_name))
