from __future__ import annotations

from functools import partial
from typing import Annotated, Union

from pydantic import Field, PrivateAttr

RawClassesPayload = Union[str, list[str], tuple[str, ...], 'Classes', None]


class Classes:
    def __init__(self, *args: RawClassesPayload):
        self._container: list[str] = []

        for arg in args:
            if isinstance(arg, str):
                self._container.append(arg)
            elif isinstance(arg, (list, tuple)):
                self._container.extend(arg)
            elif isinstance(arg, Classes):
                self._container.extend(arg._container)
            elif arg is None:
                continue
            else:
                raise TypeError(f"Expected str or list[str] or tuple[str] or None, got {type(arg)}")

    @classmethod
    def provide(
            cls, payload: RawClassesPayload = None, description: str | None = None, *, private: bool = False
    ) -> type[Classes]:
        _factory = partial(cls, payload)
        if private:
            return Annotated[cls, PrivateAttr(default_factory=partial(cls, payload))]
        else:
            return Annotated[cls, Field(default_factory=partial(cls, payload), description=description)]

    def append(self, *args: str):
        self._container.extend(args)

    def remove(self, *args: str):
        for arg in args:
            if arg in self._container:
                self._container.remove(arg)

    def toggle(self, *args: str):
        for arg in args:
            if arg in self._container:
                self._container.remove(arg)
            else:
                self._container.append(arg)

    def render(self) -> str | None:
        return None if not self._container else " ".join(self._container)
