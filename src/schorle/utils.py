import sys
from enum import Enum

from lxml import etree

from schorle.context_vars import CURRENT_PARENT
from schorle.page import Page


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


def reactive(trigger: str | None = None):
    def decorator(func):
        func.trigger = trigger
        return func

    return decorator


def render_in_context(page: Page):
    try:
        CURRENT_PARENT.set(etree.Element("fragment"))
        with page:
            page()
        return CURRENT_PARENT.get().getchildren()[0]
    finally:
        CURRENT_PARENT.set(None)
