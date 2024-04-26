import sys
from enum import Enum
from importlib.resources import files
from pathlib import Path

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


def fix_self_closing_tags(element: LXMLElement) -> None:
    for _child in element.iter():
        if len(_child) == 0 and _child.text is None:
            _child.text = ""


ASSETS_PATH = Path(str(files("schorle"))) / Path("assets")
