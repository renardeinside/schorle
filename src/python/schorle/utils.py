from __future__ import annotations

import hashlib
import sys
from enum import Enum


class RunningMode(str, Enum):
    DEV = "dev"
    PRODUCTION = "production"


def get_running_mode() -> RunningMode:
    # if uvicorn and --reload are in sys.argv, we are running in uvicorn dev mode
    _joined_argv = " ".join(sys.argv)
    if "uvicorn" in _joined_argv and "--reload" in _joined_argv:
        return RunningMode.DEV
    else:
        return RunningMode.PRODUCTION


def get_sha256_hash(string: str) -> str:
    return hashlib.sha256(string.encode()).hexdigest()[:8]
