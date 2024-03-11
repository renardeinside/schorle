from __future__ import annotations

from typing import Union

from pydantic import BaseModel, Field

RawClassesPayload = Union[str, list[str], tuple[str, ...], "Classes", None]


def parse_args(*args: RawClassesPayload) -> list[str]:
    container = []
    for arg in args:
        if isinstance(arg, str):
            container.append(arg)
        elif isinstance(arg, (list, tuple)):
            container.extend(arg)
        elif isinstance(arg, Classes):
            container.extend(arg.value)
        elif arg is None:
            pass
        else:
            msg = f"Invalid type: {type(arg)} of {arg} for Classes"
            raise TypeError(msg)
    return container


class Classes(BaseModel):
    value: list[str] = Field(default_factory=list)

    def __init__(self, *args: RawClassesPayload):
        super().__init__()
        self.value = parse_args(*args)

    def append(self, *args: RawClassesPayload):
        new_value = self.value + parse_args(*args)
        self.value = new_value
        return self

    def remove(self, *args: RawClassesPayload):
        new_value = [x for x in self.value if x not in parse_args(*args)]
        self.value = new_value
        return self

    def toggle(self, class_name: str):
        if class_name in self.value:
            self.remove(class_name)
        else:
            self.append(class_name)
        return self

    def render(self) -> str:
        return "" if not self.value else " ".join(sorted(set(self.value))).strip()

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"Classes({self.render()})"
