from pathlib import Path
from typing import Generator
import pytest
from schorle.utils import cwd
from schorle.cli import app
from typer.testing import CliRunner
from faker import Faker
import subprocess
from typing import Callable
from pathlib import Path

faker = Faker()


@pytest.fixture()
def initialized_project(
    tmp_path: Path,
) -> Generator[Path, None, None]:
    project_name = faker.word()
    with cwd(tmp_path):
        try:
            subprocess.run(["uv", "init", "--name", project_name, "--lib", "."], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(e.stderr.decode("utf-8"))
            raise e
        print("uv project initialized")
        with cwd(tmp_path):
            runner = CliRunner()
            r = runner.invoke(app, ["init", f"src/{project_name}/ui"])
            if not r.exit_code == 0:
                print(r.stderr)
                raise RuntimeError("Failed to initialize project")
            yield tmp_path

    # print(f"initializing project at {tmp_path / project_name}")
    # with cwd(tmp_path):
    #     subprocess.run(["uv", "init", "--name", project_name, "--lib", "."], check=True)
    #     print(f"uv project initialized at {tmp_path / project_name}")
    #     with cwd(tmp_path / project_name):
    #         runner = CliRunner()
    #         runner.invoke(app, ["init", "--project-path", f"src/{project_name}/ui"])
    #         yield tmp_path
