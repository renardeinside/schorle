from pathlib import Path
from schorle.common import static_template_path
from jinja2 import Template
import json
import subprocess
from pydantic import BaseModel

index_template_path = static_template_path / "index.html.jinja2"
index_template = Template(index_template_path.read_text())


class ManifestEntry(BaseModel):
    js: str
    css: str


class Manifest(BaseModel):
    data: dict[str, ManifestEntry]

    @classmethod
    def from_file(cls, project_root: Path) -> "Manifest":
        manifest_path = project_root / ".schorle" / "dist" / "manifest.json"
        if not manifest_path.exists():
            raise ValueError(f"Manifest file {manifest_path} not found")
        return Manifest(data=json.loads(manifest_path.read_text()))


def _prerender(project_root: Path, page_name: str) -> str:
    page_path = project_root / "app" / "pages" / f"{page_name}.tsx"
    if not page_path.exists():
        raise ValueError(f"Page {page_name} not found at {page_path}")

    ssr_html = subprocess.check_output(
        ["schorle-bridge", "render", str(page_path.absolute())],
        text=True,
        cwd=project_root,
    )
    return ssr_html


def render(project_root: Path, page_name: str) -> str:
    print(f"Rendering page {page_name} at {project_root}")
    ssr_html = _prerender(project_root, page_name)
    manifest = Manifest.from_file(project_root)
    manifest_entry = manifest.data[page_name]
    css_path = Path("dist") / manifest_entry.css
    js_path = Path("dist") / manifest_entry.js

    return index_template.render(
        title=page_name,
        css_path=css_path,
        js_path=js_path,
        ssr_html=ssr_html,
    )
