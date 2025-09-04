"""
Generator for the Schorle module.
This generator prepares the module for the Schorle framework.
The generated file will be located in <project_root>/__init__.py

And look like this:
```python
from pathlib import Path
from schorle.boot import bootstrap as base_bootstrap
from functools import partial
from fastapi import FastAPI
from typing import Callable
from fastapi.responses import StreamingResponse
from schorle.render import render_to_stream

project_path = Path(__file__).parent
dist_path = project_path / ".schorle" / "dist"

bootstrap: Callable[FastAPI, None] = partial(base_bootstrap, project_path=project_path, dist_path=dist_path)

# generated functions for each page
def <page_name>() -> StreamingResponse:
    return render_to_stream(project_path, '<page_name>')

def <page_name>() -> StreamingResponse:
    return render_to_stream(project_path, '<page_name>')
#

```
"""

from pathlib import Path
import ast
from typing import List


def make_imports() -> List[ast.stmt]:
    return [
        ast.ImportFrom(
            module="pathlib", names=[ast.alias(name="Path", asname=None)], level=0
        ),
        ast.ImportFrom(
            module="schorle.render",
            names=[ast.alias(name="render_to_stream", asname=None)],
            level=0,
        ),
        ast.ImportFrom(
            module="fastapi.responses",
            names=[ast.alias(name="StreamingResponse", asname=None)],
            level=0,
        ),
        ast.ImportFrom(
            module="fastapi",
            names=[ast.alias(name="FastAPI", asname=None)],
            level=0,
        ),
        ast.ImportFrom(
            module="functools",
            names=[ast.alias(name="partial", asname=None)],
            level=0,
        ),
        ast.ImportFrom(
            module="schorle.bootstrap",
            names=[ast.alias(name="bootstrap", asname="_base_bootstrap")],
            level=0,
        ),
        ast.ImportFrom(
            module="typing",
            names=[ast.alias(name="Callable", asname=None)],
            level=0,
        ),
    ]


def make_paths_assignments() -> List[ast.stmt]:
    # project_path = Path(__file__).parent
    # dist_path = project_path / ".schorle" / "dist"

    root_assign = ast.Assign(
        targets=[ast.Name(id="project_path", ctx=ast.Store())],
        value=ast.Attribute(
            value=ast.Call(
                func=ast.Name(id="Path", ctx=ast.Load()),
                args=[ast.Name(id="__file__", ctx=ast.Load())],
                keywords=[],
            ),
            attr="parent",
            ctx=ast.Load(),
        ),
    )
    dist_assign = ast.Assign(
        targets=[ast.Name(id="dist_path", ctx=ast.Store())],
        value=ast.BinOp(
            left=ast.BinOp(
                left=ast.Name(id="project_path", ctx=ast.Load()),
                op=ast.Div(),
                right=ast.Constant(value=".schorle"),
            ),
            op=ast.Div(),
            right=ast.Constant(value="dist"),
        ),
    )
    return [root_assign, dist_assign]


def make_bootstrap_function() -> ast.AnnAssign:
    # bootstrap: Callable[FastAPI, None] = partial(base_bootstrap, project_path=project_path, dist_path=dist_path)
    return ast.AnnAssign(
        target=ast.Name(id="bootstrap", ctx=ast.Store()),
        annotation=ast.Subscript(
            value=ast.Name(id="Callable", ctx=ast.Load()),
            slice=ast.Tuple(
                elts=[
                    ast.Name(id="[FastAPI]", ctx=ast.Load()),
                    ast.Constant(value=None),
                ],
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        ),
        value=ast.Call(
            func=ast.Name(id="partial", ctx=ast.Load()),
            args=[
                ast.Name(id="_base_bootstrap", ctx=ast.Load()),
                ast.Name(id="project_path", ctx=ast.Load()),
                ast.Name(id="dist_path", ctx=ast.Load()),
            ],
            keywords=[],
        ),
        simple=1,
    )


def make_page_handler(name: str) -> ast.FunctionDef:
    """
    def <page_name>() -> StreamingResponse:
        return render_to_stream(project_path, '<page_name>')
    """

    render_call = ast.Call(
        func=ast.Name(id="render_to_stream", ctx=ast.Load()),
        args=[
            ast.Name(id="project_path", ctx=ast.Load()),
            ast.Constant(value=name),
        ],
        keywords=[],
    )

    return ast.FunctionDef(
        name=name,
        args=ast.arguments(
            posonlyargs=[],
            args=[],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        ),
        decorator_list=[],
        returns=ast.Name(id="StreamingResponse", ctx=ast.Load()),
        body=[
            ast.Return(
                value=render_call,
            )
        ],
    )


def build_module(tsx_files: List[Path]) -> ast.Module:
    body: List[ast.stmt] = []
    body += make_imports()

    body += make_paths_assignments()

    body += [make_bootstrap_function()]

    for tsx in sorted(tsx_files, key=lambda p: p.name.lower()):
        page_name = tsx.stem
        body.append(make_page_handler(page_name))

    mod = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(mod)
    return mod


def generate_module(project_root: Path) -> ast.Module:
    pages_path = project_root / "app" / "pages"
    output_path = project_root / "__init__.py"
    tsx_files = [p for p in pages_path.glob("*.tsx") if p.is_file()]
    # filter out any file with __layout in the name
    tsx_files = [p for p in tsx_files if "__layout" not in p.name]

    mod = build_module(tsx_files)

    code = ast.unparse(mod)  # Python 3.9+
    output_path.write_text(
        f"# Generated file — do not edit manually\n\n{code}", encoding="utf-8"
    )
