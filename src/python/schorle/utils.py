from __future__ import annotations

import sys
from enum import Enum

from starlette.responses import HTMLResponse

from schorle.types import LXMLElement


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


def empty():
    return HTMLResponse(content="", status_code=200)


def fix_self_closing_tags(element: LXMLElement) -> None:
    for _tag in element.iter():
        if _tag.tag in ["script", "link", "i", "span"]:
            if _tag.text is None:
                _tag.text = ""
