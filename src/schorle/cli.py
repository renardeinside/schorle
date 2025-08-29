import shutil
import json
import subprocess
import typer
from pathlib import Path
import importlib.metadata
import tomlkit

__version__ = importlib.metadata.version("schorle")
static_template_path = Path(__file__).parent / "templates"

app = typer.Typer(
    name="schorle",
    help="Schorle is a framework for building powerful data-driven applications.",
)


@app.command(name="version")
def version():
    typer.echo(f"Schorle version {__version__}")


@app.command(name="init")
def init(
    project_name: str = typer.Argument(
        help="The name of the project.",
    ),
    project_path: Path = typer.Argument(
        default_factory=Path.cwd,
        help="The path to the project.",
    ),
    frontend_root_path: Path | None = typer.Option(
        None,
        help="The path to the frontend root directory (relative to the project path).",
    ),
):
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

    # run bun init
    subprocess.run(
        ["bun", "init", "-y", "-m"],
        cwd=project_path,
        check=True,
    )

    dependencies = ["react", "react-dom", "tailwindcss", "bun-plugin-tailwind"]

    dev_dependencies = [
        "@types/react",
        "@types/react-dom",
    ]

    subprocess.run(
        ["bun", "add", *dependencies],
        cwd=project_path,
        check=True,
    )

    subprocess.run(
        ["bun", "add", *dev_dependencies, "--dev"],
        cwd=project_path,
        check=True,
    )

    # update the tsconfig.json to support the ui folder
    schorle_dir = project_path / ".schorle"
    schorle_dir.mkdir(parents=True, exist_ok=True)
    tsconfig_json = schorle_dir / "tsconfig.json"
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
            "paths": {"@/*": [f"../src/{project_name}/ui/*"]},
            "noUnusedLocals": False,
            "noUnusedParameters": False,
            "noPropertyAccessFromIndexSignature": False,
        },
        "exclude": ["dist", "node_modules"],
    }

    tsconfig_json.write_text(json.dumps(tsconfig_payload, indent=2))

    tsconfig_in_root = project_path / "tsconfig.json"

    tsconfig_in_root.write_text(
        json.dumps(
            {"extends": "./.schorle/tsconfig.json"},
            indent=2,
        )
    )

    # # populate ui folder
    ui_folder = project_path / "src" / project_name / "ui"
    ui_folder.mkdir(parents=True, exist_ok=True)

    # # populate ui folder with:
    # # pages/index.tsx
    # # components/ (just a folder)
    # # index.css
    ui_folder.joinpath("pages").mkdir(parents=True, exist_ok=True)

    shutil.copy(static_template_path / "Index.tsx", ui_folder / "pages" / "Index.tsx")

    # adjust pyproject.toml
    if frontend_root_path is None:
        frontend_root_path = Path("src") / project_name / "ui"

    pyproject_toml = project_path / "pyproject.toml"
    toml_data = tomlkit.parse(pyproject_toml.read_text())
    if "tool" not in toml_data:
        toml_data["tool"] = tomlkit.table()
    if "schorle" not in toml_data["tool"]:
        toml_data["tool"]["schorle"] = tomlkit.table()

    toml_data["tool"]["schorle"]["frontend_root_path"] = str(frontend_root_path)
    pyproject_toml.write_text(tomlkit.dumps(toml_data))

    # shadcn setup
    shadcn_deps = [
        "class-variance-authority",
        "clsx",
        "tailwind-merge",
        "lucide-react",
        "tw-animate-css",
    ]

    subprocess.run(
        ["bun", "add", *shadcn_deps],
        cwd=project_path,
        check=True,
    )
    styles_dir = ui_folder / "styles"
    styles_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(static_template_path / "globals.css", styles_dir / "globals.css")

    lib_dir = ui_folder / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(static_template_path / "utils.ts", lib_dir / "utils.ts")

    components_file_payload = {
        "$schema": "https://ui.shadcn.com/schema.json",
        "style": "new-york",
        "rsc": False,
        "tsx": True,
        "tailwind": {
            "config": "",
            "css": f"src/{project_name}/ui/styles/globals.css",
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

    # add button component as example
    subprocess.run(
        ["bunx", "shadcn@latest", "add", "button"],
        cwd=project_path,
        check=True,
    )
