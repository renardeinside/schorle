from __future__ import annotations

from typing import Union

from pydantic import PrivateAttr

from schorle.reactives.base import ReactiveBase

RawClassesPayload = Union[str, list[str], tuple[str, ...], "Classes", None]


def parse_args(*args: RawClassesPayload) -> list[str]:
    container = []
    for arg in args:
        if isinstance(arg, str):
            container.append(arg)
        elif isinstance(arg, (list, tuple)):
            container.extend(arg)
        elif isinstance(arg, Classes):
            container.extend(arg.get())
        elif arg is None:
            pass
        else:
            msg = f"Invalid type: {type(arg)} of {arg} for Classes"
            raise TypeError(msg)
    return container


class Classes(ReactiveBase[list[str]]):
    _value: list[str] = PrivateAttr(default_factory=list)

    def __init__(self, *args: RawClassesPayload):
        super().__init__()
        self._value = parse_args(*args)

    async def append(self, *args: RawClassesPayload):
        await self.update(self._value + parse_args(*args))

    async def remove(self, *args: RawClassesPayload):
        new_value = [x for x in self._value if x not in parse_args(*args)]
        await self.update(new_value)

    async def toggle(self, class_name: str):
        if class_name in self._value:
            await self.remove(class_name)
        else:
            await self.append(class_name)

    def render(self) -> str | None:
        return None if not self.get() else " ".join(self.get())
