from __future__ import annotations

from typing import Any, Callable, Union

from pydantic import BaseModel, PrivateAttr
from pydantic.dataclasses import dataclass

from schorle.state import ReactiveModel

RawClassesPayload = Union[str, list[str], tuple[str, ...], "Classes", None]


def parse_args(*args: RawClassesPayload) -> list[str]:
    container = []
    for arg in args:
        if isinstance(arg, str):
            container.append(arg)
        elif isinstance(arg, (list, tuple)):
            container.extend(arg)
        elif isinstance(arg, Classes):
            container.extend(arg._value)
        elif arg is None:
            pass
        else:
            msg = f"Invalid type: {type(arg)} of {arg} for Classes"
            raise TypeError(msg)
    return container


class Classes(BaseModel):
    _value: list[str] = PrivateAttr(default_factory=list)

    def __init__(self, *args: RawClassesPayload):
        super().__init__()
        self._value = parse_args(*args)

    def append(self, *args: RawClassesPayload):
        new_value = self._value + parse_args(*args)
        self._value = new_value
        return self

    def remove(self, *args: RawClassesPayload):
        new_value = [x for x in self._value if x not in parse_args(*args)]
        self._value = new_value
        return self

    def toggle(self, class_name: str):
        if class_name in self._value:
            self.remove(class_name)
        else:
            self.append(class_name)
        return self

    def render(self) -> str:
        return "" if not self._value else " ".join(sorted(set(self._value))).strip()

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"Classes({self.render()})"


@dataclass
class On:
    trigger: str
    callback: Callable
    ws_based: bool = True


@dataclass
class Suspense:
    on: ReactiveModel
    fallback: Callable
    parent: Any | None = None

    def render(self):
        with self.parent():
            self.fallback()
