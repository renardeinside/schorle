from pathlib import Path
import subprocess
import typer
import importlib.metadata
import importlib.resources
from tomlkit import parse, dumps, table
from schorle.build import build_entrypoints
from schorle.bun import check_and_prepare_bun
from schorle.page_system import generate_python_stubs
from schorle.utils import find_schorle_project

__version__ = importlib.metadata.version("schorle")
templates_path = importlib.resources.files("schorle").joinpath("templates")

app = typer.Typer(
    name="slx",
    help="Schorle is a framework for building powerful data-driven applications.",
)


@app.command(name="version", help="Show the version of the schorle CLI")
def version():
    typer.echo(f"Schorle version {__version__}")


@app.command(name="init", help="Initialize a new project")
def init(
    project_path: Path = typer.Argument(
        default_factory=lambda: Path.cwd(),
        help="The path to the project, usually ui or src/{python_project_name}/ui",
    ),
):
    typer.echo(f"Generating project at {project_path}")
    root_path = Path.cwd()

    if project_path.exists():
        typer.echo(f"Project path {project_path} already exists")
        raise typer.Exit(code=1)

    # check if pyproject.toml exists in root_path
    pyproject_toml_path = root_path / "pyproject.toml"
    if not pyproject_toml_path.exists():
        typer.echo(f"pyproject.toml not found in {root_path}, it will be created")

    doc = (
        parse(pyproject_toml_path.read_text())
        if pyproject_toml_path.exists()
        else table()
    )

    if "tool" not in doc:
        doc["tool"] = table()

    if "schorle" not in doc["tool"]:  # type: ignore
        doc["tool"]["schorle"] = table()  # type: ignore

    doc["tool"]["schorle"]["project_root"] = str(project_path)  # type: ignore

    pyproject_toml_path.write_text(dumps(doc))

    project_path.mkdir(parents=True, exist_ok=True)

    pages_path = project_path / "pages"
    pages_path.mkdir(parents=True, exist_ok=True)

    components_path = project_path / "components"
    components_path.mkdir(parents=True, exist_ok=True)

    styles_path = project_path / "styles"
    styles_path.mkdir(parents=True, exist_ok=True)

    lib_path = project_path / "lib"
    lib_path.mkdir(parents=True, exist_ok=True)

    tsconfig_path = root_path / "tsconfig.json"
    tsconfig_path.write_text(templates_path.joinpath("tsconfig.json").read_text())

    package_json_path = root_path / "package.json"
    package_json_path.write_text(templates_path.joinpath("package.json").read_text())

    components_path = root_path / "components.json"
    components_path.write_text(templates_path.joinpath("components.json").read_text())

    utils_path = project_path / "lib/utils.ts"
    utils_path.write_text(templates_path.joinpath("utils.ts").read_text())

    globals_css_path = project_path / "styles/globals.css"
    globals_css_path.write_text(templates_path.joinpath("globals.css").read_text())

    pages_path = project_path / "pages/Index.tsx"
    pages_path.write_text(templates_path.joinpath("Index.tsx").read_text())

    layout_path = project_path / "pages/__layout.tsx"
    layout_path.write_text(templates_path.joinpath("__layout.tsx").read_text())

    counter_path = project_path / "components/Counter.tsx"
    counter_path.write_text(templates_path.joinpath("Counter.tsx").read_text())

    dev_helper_path = project_path / "components" / "dev" / "SchorleDevHelper.tsx"
    dev_helper_path.parent.mkdir(parents=True, exist_ok=True)
    dev_helper_path.write_text(
        templates_path.joinpath("SchorleDevHelper.tsx").read_text()
    )

    bun_executable = check_and_prepare_bun()

    subprocess.run(
        [bun_executable, "x", "--bun", "shadcn@latest", "add", "button"],
        cwd=root_path,
    )

    # check if .gitignore exists in root_path

    ignorables = ["node_modules", ".schorle"]

    gitignore_path = root_path / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text("\n".join(ignorables))
    else:
        # check if ignorables are in .gitignore
        to_be_added = []
        for ignoreable in ignorables:
            if ignoreable not in gitignore_path.read_text():
                to_be_added.append(ignoreable)
        if to_be_added:
            gitignore_path.write_text("\n".join(to_be_added))

    typer.echo("Project initialized successfully")


@app.command(name="build", help="Build the project")
def build(
    dev: bool = typer.Option(False, help="Build in dev mode"),
    with_stubs: bool = typer.Option(True, help="Generate Python stubs for pages"),
):
    typer.echo("Building project")
    project = find_schorle_project(Path.cwd())
    project.dev = dev

    build_entrypoints(("bun", "run", "slx-ipc", "build"), project)
    if with_stubs:
        generate_python_stubs(project)
