import json
from pathlib import Path
import subprocess
import shutil
import time
from fastapi import FastAPI
import typer
import importlib.metadata
from tomlkit import parse, dumps, table
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from schorle.build import build_entrypoints
from schorle.bun import check_and_prepare_bun
from schorle.json_schema import generate_schemas
from schorle.page_system import generate_python_stubs
from schorle.utils import schema_to_ts, templates_path
from schorle.manifest import find_schorle_project

__version__ = importlib.metadata.version("schorle")

console = Console()

app = typer.Typer(
    name="slx",
    help="Schorle is a framework for building powerful data-driven applications.",
    pretty_exceptions_short=True,
)


@app.command(name="version", help="Show the version of the schorle CLI")
def version():
    console.print(f"[blue]●[/blue] Schorle version {__version__}")


@app.command(name="init", help="Initialize a new project")
def init(
    project_path: Path = typer.Argument(
        default_factory=lambda: Path.cwd(),
        help="The path to the project, usually ui or src/{python_project_name}/ui",
    ),
):
    console.print(f"[blue]●[/blue] Generating project at {project_path}")
    root_path = Path.cwd()

    if project_path.exists():
        console.print(f"[red]✗[/red] Project path {project_path} already exists")
        raise typer.Exit(code=1)

    # check if pyproject.toml exists in root_path
    pyproject_toml_path = root_path / "pyproject.toml"
    if not pyproject_toml_path.exists():
        console.print(
            f"[yellow]⚠[/yellow] pyproject.toml not found in {root_path}, it will be created"
        )

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

    console.print("[blue]●[/blue] [green]Project initialized successfully[/green]")


@app.command(name="build", help="Build the project")
def build(
    dev: bool = typer.Option(False, help="Build in dev mode"),
    with_stubs: bool = typer.Option(True, help="Generate Python stubs for pages"),
):
    project = find_schorle_project(Path.cwd())
    project.dev = dev

    console.print(f"Building project in {'dev' if dev else 'prod'} mode", style="blue")

    # Create spinner with blue dot
    spinner = Spinner("dots", text="Building project...", style="blue")

    with Live(spinner, console=console, refresh_per_second=10):
        start_time = time.time()

        # Build entrypoints
        build_entrypoints(("bun", "run", "slx-ipc", "build"), project)

        # Generate Python stubs if requested
        if with_stubs:
            spinner.update(text="Generating Python stubs...")
            generate_python_stubs(project)

        end_time = time.time()
        build_time_ms = (end_time - start_time) * 1000
        spinner.update(text="Build completed successfully", style="green")

    # Show completion message with blue dot and timing
    success_text = Text()
    success_text.append("● ", style="blue bold")
    success_text.append(
        f"Build completed successfully in {build_time_ms:.1f}ms", style="green"
    )
    # show the manifest path
    console.print(f"Manifest file generated at: {project.manifest_path}", style="blue")
    console.print(f"Total pages: {len(project.manifest.entries)}", style="blue")
    # tell how many pages are in the manifest
    console.print(success_text)


@app.command("codegen", help="Generate models from the project")
def generate_models(
    module_name: str = typer.Argument(
        help="The name of the module to generate models for",
    ),
):
    project = find_schorle_project(Path.cwd())

    console.print(
        f"Generating models for module: [bold]{module_name}[/bold]", style="blue"
    )

    # Create spinner with blue dot
    spinner = Spinner(
        "dots", text="Importing module and generating schemas...", style="blue"
    )

    with Live(spinner, console=console, refresh_per_second=10):
        start_time = time.time()

        # Generate models
        bun_executable = check_and_prepare_bun()
        module = importlib.import_module(module_name)

        spinner.update(text="Generating JSON schemas...")
        json_schema = generate_schemas(module)

        spinner.update(text="Converting to TypeScript definitions...")
        ts_schema = schema_to_ts(json_schema, bun_executable)

        project.types_path.mkdir(parents=True, exist_ok=True)
        output_path = project.types_path / f"{module_name}.d.ts"

        spinner.update(text="Writing TypeScript definitions...")

        barrel_file = project.types_path / "index.d.ts"
        # check if barrel_file exists
        if not barrel_file.exists():
            barrel_file.write_text(
                "\n".join(
                    [
                        f"export * from './{module_name}.d.ts';",
                    ]
                )
            )
        else:
            # check if export * from './{module_name}.d.ts'; exists, add it if not
            if f"export * from './{module_name}.d.ts';" not in barrel_file.read_text():
                current_content = barrel_file.read_text()
                barrel_file.write_text(
                    current_content + f"\nexport * from './{module_name}.d.ts';"
                )
        current_ts_content = (
            output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        )
        if ts_schema != current_ts_content:
            output_path.write_text(ts_schema, encoding="utf-8")

        end_time = time.time()
        generation_time_ms = (end_time - start_time) * 1000
        spinner.update(text="Models generated successfully", style="green")

    # Show completion message with blue dot and timing
    success_text = Text()
    success_text.append("● ", style="blue bold")
    success_text.append(
        f"Models generated successfully in {generation_time_ms:.1f}ms", style="green"
    )
    console.print(f"TypeScript definitions written to: {output_path}", style="blue")
    console.print(f"Barrel file updated at: {barrel_file}", style="blue")
    console.print(success_text)


@app.command("generate-api-client", help="Generate API client from OpenAPI schema")
def generate_api_client(
    app: str | None = typer.Argument(
        help="The name of the FastAPI app to generate the API client for, in format of uvicorn pkg.module:app",
    ),
):
    project = find_schorle_project(Path.cwd())

    console.print(
        f"Generating API client{f' from app: [bold]{app}[/bold]' if app else ''}",
        style="blue",
    )

    # Create spinner with blue dot
    spinner = Spinner("dots", text="Preparing API client generation...", style="blue")

    with Live(spinner, console=console, refresh_per_second=10):
        start_time = time.time()

        if app is not None:
            spinner.update(text="Loading FastAPI app and extracting OpenAPI schema...")
            module = importlib.import_module(app.split(":")[0])
            instance: FastAPI = getattr(module, app.split(":")[1])
            schema = instance.openapi()

            if not project.api_client_temp_path.exists():
                project.api_client_temp_path.mkdir(parents=True, exist_ok=True)

            spinner.update(text="Writing OpenAPI schema to file...")
            (project.api_client_temp_path / "api.json").write_text(
                json.dumps(schema, indent=2)
            )
        else:
            spinner.update(text="Using existing API schema file...")

        # Check if API schema file exists
        api_schema_path = project.api_client_temp_path / "api.json"
        if not api_schema_path.exists():
            # Exit the spinner context to show error messages
            pass  # Will exit the Live context and show error after

        # Ensure temp path exists
        project.api_client_temp_path.mkdir(parents=True, exist_ok=True)

        # Determine orval config path
        spinner.update(text="Setting up orval configuration...")
        if project.user_provided_orval_config_path.exists():
            orval_config_path = project.user_provided_orval_config_path
        else:
            if not project.default_orval_config_path.exists():
                # copy template
                project.default_orval_config_path.parent.mkdir(
                    parents=True, exist_ok=True
                )
                shutil.copy(
                    project.orval_config_template_path,
                    project.default_orval_config_path,
                )
            orval_config_path = project.default_orval_config_path

        # Generate client using orval
        spinner.update(text="Running orval to generate API client...")
        bun_executable = check_and_prepare_bun()

        result = subprocess.run(
            [
                str(bun_executable),
                "x",
                "orval",
                "--config",
                str(orval_config_path),
                "--output",
                str(project.api_client_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        end_time = time.time()
        generation_time_ms = (end_time - start_time) * 1000

        if result.returncode != 0:
            spinner.update(text="API client generation failed", style="red")
        else:
            spinner.update(text="API client generated successfully", style="green")

    # Check for missing schema file outside Live context
    if not api_schema_path.exists():
        console.print(f"[red]✗[/red] API schema file not found at {api_schema_path}")
        console.print(
            "[yellow]⚠[/yellow] Make sure to run this after the FastAPI app has generated the schema"
        )
        raise typer.Exit(code=1)

    # Handle subprocess errors outside Live context
    if result.returncode != 0:
        console.print(
            f"[red]✗[/red] Error generating API client after {generation_time_ms:.1f}ms"
        )
        if result.stderr:
            console.print(f"[red]Error details:[/red] {result.stderr}")
        raise typer.Exit(code=1)

    # Show completion message with blue dot and timing
    success_text = Text()
    success_text.append("● ", style="blue bold")
    success_text.append(
        f"API client generated successfully in {generation_time_ms:.1f}ms",
        style="green",
    )
    console.print(f"API client generated at: {project.api_client_path}", style="blue")
    console.print(f"Using orval config: {orval_config_path}", style="blue")
    if result.stderr:
        console.print(f"[red]Error details:[/red] {result.stderr}", style="red")
        raise typer.Exit(code=1)
    console.print(success_text)


add_app = typer.Typer(
    name="add",
    help="Add components or dependencies to the project",
)
app.add_typer(add_app, name="add")


component_args = {
    "help": """Add a component to the project.

    This command will run `bun x shadcn@latest add component` with the remaining arguments.

    Example:

    > slx add component button
    """,
    "context_settings": {"allow_extra_args": True, "ignore_unknown_options": True},
}


@add_app.command("component", **component_args)  # type: ignore
@add_app.command("comp", **component_args)  # type: ignore
@add_app.command("c", **component_args)  # type: ignore
def add_component(
    ctx: typer.Context,
):
    bun_executable = check_and_prepare_bun()
    project = find_schorle_project(Path.cwd())

    # run bun x shadcn@latest add component with the remaining arguments
    subprocess.run(
        [bun_executable, "x", "shadcn@latest", "add", *ctx.args], cwd=project.root_path
    )


dependency_args = {
    "help": """Add a dependency to the project.

    This command will run `bun add` with the remaining arguments.
    """,
    "context_settings": {"allow_extra_args": True, "ignore_unknown_options": True},
}


@add_app.command("dependency", **dependency_args)  # type: ignore
@add_app.command("dep", **dependency_args)  # type: ignore
@add_app.command("d", **dependency_args)  # type: ignore
def add_dependency(
    ctx: typer.Context,
):
    bun_executable = check_and_prepare_bun()
    project = find_schorle_project(Path.cwd())

    # run bun add with the remaining arguments
    subprocess.run([bun_executable, "add", *ctx.args], cwd=project.root_path)
