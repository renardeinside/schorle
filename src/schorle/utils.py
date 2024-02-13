import sys
from enum import Enum

from lxml import etree

from schorle.component import Component
from schorle.context_vars import CURRENT_PARENT


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


def render_in_context(component: Component):
    try:
        CURRENT_PARENT.set(etree.Element("root"))
        component()
        return CURRENT_PARENT.get().getchildren()[0]
    finally:
        CURRENT_PARENT.set(None)
