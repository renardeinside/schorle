from dataclasses import dataclass
from typing import Callable

from schorle.reactive import Reactive


@dataclass
class On:
    event: str
    handler: Callable


@dataclass
class Bind:
    property: str
    reactive: Reactive


class _When:
    def __init__(self, reactive: Reactive[bool] | bool):
        self.reactive = reactive if isinstance(reactive, Reactive) else Reactive(reactive)
        self._classes_in_condition: str | None = None

    def then(self, classes: str):
        self._classes_in_condition = classes
        return self

    def otherwise(self, classes: str):
        return self._classes_in_condition if self.reactive.rx else classes

    def __str__(self):
        return self._classes_in_condition if self.reactive.rx else ""


def when(reactive: Reactive[bool] | bool) -> _When:
    return _When(reactive)
