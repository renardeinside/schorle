from pathlib import Path
from typing import Callable
from watchfiles import awatch


async def dev_watcher(path: Path, reload_callbacks: list[Callable[[], None]]):
    async for changes in awatch(path):
        for reload_callback in reload_callbacks:
            reload_callback()
