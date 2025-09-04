import shutil
import json
import subprocess
import typer
from pathlib import Path
import importlib.metadata

from schorle.common import static_template_path
from schorle.generator import generate_module
from schorle.render import render_to_stream

__version__ = importlib.metadata.version("schorle")


app = typer.Typer(
    name="schorle",
    help="Schorle is a framework for building powerful data-driven applications.",
)


@app.command(name="version")
def version():
    typer.echo(f"Schorle version {__version__}")


@app.command(name="init")
def init(
    project_path: Path = typer.Argument(
        default_factory=Path.cwd,
        help="The path to the project.",
    ),
):
    schorle_path = project_path / ".schorle"
    schorle_path.mkdir(parents=True, exist_ok=True)

    app_path = project_path / "app"
    app_path.mkdir(parents=True, exist_ok=True)

    # run bun init
    subprocess.run(
        ["bun", "init", "-y", "-m"],
        cwd=project_path,
        check=True,
    )

    subprocess.run(
        [
            "bun",
            "add",
            f"{Path(__file__).parent.parent.parent}/.dev/schorle-bridge-0.0.1.tgz",
            "--dev",
        ],
        cwd=project_path,
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

    tsconfig_in_ui = project_path / "tsconfig.json"
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
        cwd=project_path,
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

    components_file = project_path / "components.json"
    components_file.write_text(json.dumps(components_file_payload, indent=2))

    # add theme components
    shutil.copytree(static_template_path / "theme", app_path / "components" / "theme")

    # add root layout
    shutil.copy(
        static_template_path / "__layout.tsx", app_path / "pages" / "__layout.tsx"
    )

    # add schorle-level gitignore
    ui_gitignore = project_path / ".gitignore"
    shutil.copy(static_template_path / ".ui_gitignore", ui_gitignore)

    # add models.py
    shutil.copy(static_template_path / "models.py", project_path / "models.py")

    # add button component
    subprocess.run(
        ["bunx", "shadcn@latest", "add", "button"],
        cwd=project_path,
        check=True,
    )

    build(project_path)

    subprocess.run(
        ["git", "init"],
        cwd=project_path,
        check=True,
    )


@app.command(name="build")
def build(
    project_path: Path = typer.Argument(
        default_factory=Path.cwd,
        help="The path to the project.",
    ),
):
    if not project_path.exists():
        raise typer.BadParameter(f"Project path {project_path} does not exist.")

    command = [
        "bun",
        "run",
        "schorle-bridge",
        "build",
    ]

    subprocess.run(
        command,
        cwd=project_path,
        check=True,
    )

    generate_module(project_path)


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

    stream = render_to_stream(project_path, page_name)

    import asyncio

    async def _main():
        async for chunk in stream.body_iterator:
            typer.echo(chunk)

    asyncio.run(_main())
