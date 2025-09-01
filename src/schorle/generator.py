from pathlib import Path
import ast
from typing import List


def to_pascal(name: str) -> str:
    # Strip extension, split on non-alnum boundaries, and PascalCase it
    base = Path(name).stem
    parts = []
    buf = []
    for ch in base:
        if ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                parts.append("".join(buf))
                buf = []
    if buf:
        parts.append("".join(buf))
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def make_imports() -> List[ast.stmt]:
    return [
        ast.ImportFrom(
            module="pathlib", names=[ast.alias(name="Path", asname=None)], level=0
        ),
        ast.ImportFrom(
            module="fastapi.responses",
            names=[ast.alias(name="HTMLResponse", asname=None)],
            level=0,
        ),
        ast.ImportFrom(
            module="schorle.render",
            names=[ast.alias(name="render", asname=None)],
            level=0,
        ),
        ast.ImportFrom(
            module="fastapi.staticfiles",
            names=[ast.alias(name="StaticFiles", asname=None)],
            level=0,
        ),
        ast.ImportFrom(
            module="fastapi",
            names=[ast.alias(name="FastAPI", asname=None)],
            level=0,
        ),
        ast.ImportFrom(
            module="schorle.cli",
            names=[ast.alias(name="build", asname=None)],
            level=0,
        ),
    ]


classmethod_decorator = ast.Name(id="classmethod", ctx=ast.Load())


def make_paths_assignments() -> List[ast.stmt]:
    # root_path = Path(__file__).parent
    root_assign = ast.Assign(
        targets=[ast.Name(id="root_path", ctx=ast.Store())],
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
    # dist_path = root_path / ".schorle" / "dist"
    dist_assign = ast.Assign(
        targets=[ast.Name(id="dist_path", ctx=ast.Store())],
        value=ast.BinOp(
            left=ast.BinOp(
                left=ast.Name(id="root_path", ctx=ast.Load()),
                op=ast.Div(),
                right=ast.Constant(value=".schorle"),
            ),
            op=ast.Div(),
            right=ast.Constant(value="dist"),
        ),
    )
    return [root_assign, dist_assign]


def make_mount_assets_function() -> ast.FunctionDef:
    # def mount_assets(app: FastAPI) -> None:
    #     app.mount("/dist", StaticFiles(directory=dist_path))
    return ast.FunctionDef(
        name="mount_assets",
        args=ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(arg="app", annotation=ast.Name(id="FastAPI", ctx=ast.Load()))
            ],  # add annotation if you like: ast.arg(arg="app", annotation=ast.Name(id="FastAPI", ctx=ast.Load()))
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        ),
        body=[
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="build", ctx=ast.Load()),
                    args=[ast.Name(id="root_path", ctx=ast.Load())],
                    keywords=[],
                )
            ),
            ast.Expr(  # statements must be wrapped in Expr if they’re calls
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="app", ctx=ast.Load()),
                        attr="mount",
                        ctx=ast.Load(),
                    ),
                    args=[
                        ast.Constant(value="/.schorle/dist"),
                        ast.Call(
                            func=ast.Name(id="StaticFiles", ctx=ast.Load()),
                            args=[],
                            keywords=[
                                ast.keyword(
                                    arg="directory",
                                    value=ast.Name(id="dist_path", ctx=ast.Load()),
                                )
                            ],
                        ),
                    ],
                    keywords=[],
                )
            ),
        ],
        decorator_list=[],
        returns=None,  # or ast.Name(id="None", ctx=ast.Load()) for an explicit annotation
        type_comment=None,
    )


def make_page_handler(name: str) -> ast.FunctionDef:
    """
    def <page_name>() -> HTMLResponse:
        return HTMLResponse(content=render(root_path, <page_name>), media_type="text/html")
    """

    render_call = ast.Call(
        func=ast.Name(id="render", ctx=ast.Load()),
        args=[
            ast.Name(id="root_path", ctx=ast.Load()),
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
        returns=ast.Name(id="HTMLResponse", ctx=ast.Load()),
        body=[
            ast.Return(
                value=ast.Call(
                    func=ast.Name(id="HTMLResponse", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="content",
                            value=render_call,
                        ),
                        ast.keyword(
                            arg="media_type",
                            value=ast.Constant(value="text/html"),
                        ),
                    ],
                )
            )
        ],
    )


def build_module(tsx_files: List[Path], class_casing: str) -> ast.Module:
    body: List[ast.stmt] = []
    body += make_imports()

    body += make_paths_assignments()

    body += [make_mount_assets_function()]

    for tsx in sorted(tsx_files, key=lambda p: p.name.lower()):
        page_name = tsx.stem if class_casing == "exact" else to_pascal(tsx.name)
        # Ensure valid identifier (fallback if needed)
        if not page_name.isidentifier():
            page_name = to_pascal(tsx.name)
        body.append(make_page_handler(page_name))

    mod = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(mod)
    return mod


def generate_module(project_root: Path, class_casing: str = "exact") -> ast.Module:
    pages_path = project_root / "app" / "pages"
    output_path = project_root / "__init__.py"
    tsx_files = [p for p in pages_path.glob("*.tsx") if p.is_file()]
    # filter out any file with __layout in the name
    tsx_files = [p for p in tsx_files if "__layout" not in p.name]

    mod = build_module(tsx_files, class_casing=class_casing)

    code = ast.unparse(mod)  # Python 3.9+
    output_path.write_text(
        f"# Generated file — do not edit manually\n\n{code}", encoding="utf-8"
    )
