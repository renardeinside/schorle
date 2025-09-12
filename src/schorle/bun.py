import os
import shutil
import platform
import tempfile
import zipfile
from pathlib import Path

import requests

BUN_VERSION = "1.2.21"


def bun_installed() -> bool:
    return shutil.which("bun") is not None


def install_bun(path: Path, version: str = BUN_VERSION):
    print(f"[schorle] Bun not found, installing v{version}...")

    system = platform.system().lower()
    arch = platform.machine().lower()

    # Map arch to bun’s naming scheme
    if arch in ("x86_64", "amd64"):
        arch = "x64"
    elif arch in ("aarch64", "arm64"):
        arch = "aarch64"

    url = f"https://github.com/oven-sh/bun/releases/download/bun-v{version}/bun-{system}-{arch}.zip"

    # Create target directory
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)

    # Download archive
    print(f"[schorle] Downloading from {url}")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "bun.zip"
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        # Extract archive
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        # Bun release zips contain a `bun-<system>-<arch>` folder
        extracted_root = next(Path(tmpdir).iterdir())
        print(f"[schorle] Extracted to temp: {extracted_root}")

        # Move contents into target path
        for item in extracted_root.iterdir():
            target = path / item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(item), str(target))


def check_and_prepare_bun() -> Path:
    bun = bun_installed()
    if not bun:
        user_dir = Path.home() / ".schorle"
        user_dir.mkdir(parents=True, exist_ok=True)
        install_bun(user_dir)
        bun_path = user_dir / "bun"
        os.environ["PATH"] = str(bun_path) + os.pathsep + os.environ["PATH"]

    post_check_bun_path = shutil.which("bun")
    if not post_check_bun_path:
        raise RuntimeError(
            "Bun not found even after installation. Please check your PATH."
        )
    return Path(post_check_bun_path)
