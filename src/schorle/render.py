from pathlib import Path
import shlex

from fastapi.responses import StreamingResponse
import subprocess


def render_to_stream(project_root: Path, page_name: str) -> StreamingResponse:
    page_path = project_root / "app" / "pages" / f"{page_name}.tsx"
    if not page_path.exists():
        raise ValueError(f"Page {page_name} not found at {page_path}")

    cmd = f"bun run schorle-bridge render {page_name}"

    proc = subprocess.Popen(
        shlex.split(cmd),
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )

    if proc.returncode is not None:
        raise ValueError(f"Failed to render {page_name}: {proc.stderr.read().decode()}")

    def _generator():
        while True:
            chunk = proc.stdout.read(1024)
            if not chunk:
                break
            yield chunk

    return StreamingResponse(_generator(), media_type="text/html")
