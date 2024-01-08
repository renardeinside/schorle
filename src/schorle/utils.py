import sys
from asyncio import iscoroutinefunction
from enum import Enum
from typing import Callable

from schorle.observable import ObservableModel


def wrap_in_coroutine(effect: Callable[[ObservableModel], None]):
    # wrap the effect in a coroutine if it isn't one

    if not iscoroutinefunction(effect):

        async def _effect(obs: ObservableModel):
            effect(obs)

    else:
        _effect = effect
    return _effect


class RunningMode(str, Enum):
    UVICORN_DEV = "uvicorn_dev"
    PRODUCTION = "production"


def get_running_mode() -> RunningMode:
    # if uvicorn and --reload are in sys.argv, we are running in uvicorn dev mode
    _joined_argv = " ".join(sys.argv)
    if "uvicorn" in _joined_argv and "--reload" in _joined_argv:
        return RunningMode.UVICORN_DEV
    else:
        return RunningMode.PRODUCTION
