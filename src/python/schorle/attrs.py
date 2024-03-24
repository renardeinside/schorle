from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Union

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


@dataclass
class On:
    trigger: str
    callback: Any


class HTTPMethod(str, Enum):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class Action:
    method: HTTPMethod
    url: str


def post(url: str):
    return Action(method=HTTPMethod.POST, url=url)


def get(url: str):
    return Action(method=HTTPMethod.GET, url=url)


def put(url: str):
    return Action(method=HTTPMethod.PUT, url=url)


def delete(url: str):
    return Action(method=HTTPMethod.DELETE, url=url)


def patch(url: str):
    return Action(method=HTTPMethod.PATCH, url=url)


class Swap(str, Enum):
    morph = "morph"
    after_end = "afterend"
    before_begin = "beforebegin"
    before_end = "beforeend"
    outer_html = "outerHtml"
    inner_html = "innerHtml"


@dataclass
class Handler:
    action: Action
    target: str
    swap: str | Swap = Swap.morph
    trigger: str | None = None

    def render(self) -> dict[str, str]:
        _rendered = {}

        if self.trigger:
            _rendered["hx-trigger"] = self.trigger

        _rendered.update(
            {
                "hx-swap": self.swap,
                "hx-target": self.target,
                "hx-" + self.action.method.lower(): self.action.url,
            }
        )
        return _rendered
