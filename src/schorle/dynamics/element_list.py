from __future__ import annotations

from typing import TypeVar

from schorle.dynamics.base import DynamicElement

T = TypeVar("T")  # todo- add strict typing for Element


class Collection(DynamicElement[list[T]]):
    def __init__(self, value: list[T] | None = None):
        super().__init__(value=value)

    def __repr__(self):
        return f"<ElementList {self._value}>"

    def __str__(self):
        return f"<ElementList {self._value}>"
