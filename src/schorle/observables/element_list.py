from __future__ import annotations

from typing import TypeVar

from schorle.observables.base import Observable

T = TypeVar("T")  # todo- add strict typing for Element


class ElementList(Observable[list[T]]):
    def __init__(self, value: list[T] | None = None):
        super().__init__(value=value)

    def __repr__(self):
        return f"<ElementList {self._value}>"

    def __str__(self):
        return f"<ElementList {self._value}>"