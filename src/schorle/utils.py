import sys
from enum import Enum

from schorle.component import Component
from schorle.context_vars import RENDER_CONTROLLER, RenderController
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


def render_in_context(component: Component) -> LXMLElement:
    try:
        component()
        return RENDER_CONTROLLER.get().get_root().getchildren()[0]
    finally:
        RENDER_CONTROLLER.set(RenderController())
