from __future__ import annotations

from typing import TypeVar

from schorle.reactives.base import Reactive

T = TypeVar("T")  # todo- add strict typing for Element


class Collection(Reactive[list[T]]):
    def __init__(self, value: list[T] | None = None):
        super().__init__(value=value)

    def __repr__(self):
        return f"<Collection {self._value}>"

    def __str__(self):
        return f"<Collection {self._value}>"