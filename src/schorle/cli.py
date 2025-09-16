import json
from pathlib import Path
import subprocess
import shutil
from fastapi import FastAPI
import typer
import importlib.metadata
from tomlkit import parse, dumps, table
from schorle.build import build_entrypoints
from schorle.bun import check_and_prepare_bun
from schorle.json_schema import generate_schemas
from schorle.page_system import generate_python_stubs
from schorle.utils import schema_to_ts, templates_path
from schorle.manifest import find_schorle_project

__version__ = importlib.metadata.version("schorle")


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


@app.command("codegen", help="Generate models from the project")
def generate_models(
    module_name: str = typer.Argument(
        help="The name of the module to generate models for",
    ),
):
    project = find_schorle_project(Path.cwd())

    # generate models
    bun_executable = check_and_prepare_bun()
    module = importlib.import_module(module_name)
    json_schema = generate_schemas(module)
    ts_schema = schema_to_ts(json_schema, bun_executable)

    project.types_path.mkdir(parents=True, exist_ok=True)
    output_path = project.types_path / f"{module_name}.d.ts"
    typer.echo(f"Writing models to {output_path}")

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


@app.command("generate-api-client", help="Generate API client from OpenAPI schema")
def generate_api_client(
    app: str | None = typer.Argument(
        help="The name of the FastAPI app to generate the API client for, in format of uvicorn pkg.module:app",
    ),
):
    project = find_schorle_project(Path.cwd())
    if app is not None:
        module = importlib.import_module(app.split(":")[0])
        instance: FastAPI = getattr(module, app.split(":")[1])
        schema = instance.openapi()

        if not project.api_client_temp_path.exists():
            project.api_client_temp_path.mkdir(parents=True, exist_ok=True)

        (project.api_client_temp_path / "api.json").write_text(
            json.dumps(schema, indent=2)
        )
    else:
        typer.echo("No app provided, assuming .schorle/api.json exists")

    # Check if API schema file exists
    api_schema_path = project.api_client_temp_path / "api.json"
    if not api_schema_path.exists():
        typer.echo(f"API schema file not found at {api_schema_path}")
        typer.echo(
            "Make sure to run this after the FastAPI app has generated the schema"
        )
        raise typer.Exit(code=1)

    typer.echo("Generating API client")

    # Ensure temp path exists
    project.api_client_temp_path.mkdir(parents=True, exist_ok=True)

    # Determine orval config path
    if project.user_provided_orval_config_path.exists():
        orval_config_path = project.user_provided_orval_config_path
        typer.echo(f"Using user-provided orval config: {orval_config_path}")
    else:
        if not project.default_orval_config_path.exists():
            # copy template
            project.default_orval_config_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(
                project.orval_config_template_path,
                project.default_orval_config_path,
            )
            typer.echo("Created default orval config from template")
        orval_config_path = project.default_orval_config_path
        typer.echo(f"Using default orval config: {orval_config_path}")

    # Generate client using orval
    bun_executable = check_and_prepare_bun()
    try:
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
            check=True,
            text=True,
        )
        typer.echo(f"API client generated successfully at {project.api_client_path}")
        if result.stdout:
            typer.echo(f"Output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error generating API client: {e}")
        if e.stderr:
            typer.echo(f"Error details: {e.stderr}")
        raise typer.Exit(code=1)


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
