from __future__ import annotations

from typing import Union

RawClassesPayload = Union[str, list[str], tuple[str, ...], "Classes", None]


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
                msg = f"Expected str or list[str] or tuple[str] or None, got {type(arg)}"
                raise msg

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
