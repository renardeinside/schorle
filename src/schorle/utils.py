from asyncio import iscoroutinefunction
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
