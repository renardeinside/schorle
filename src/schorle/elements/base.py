from contextvars import ContextVar
from typing import ClassVar

from schorle.elements.tags import HTMLTag

CurrentLayout: ContextVar["Layout"] = ContextVar("CurrentLayout")


def _get_current_layout():
    return CurrentLayout.get(None)


class Layout:
    def __init__(self, element: "Element"):
        self.element = element
        self._previous_layout = None

    def __enter__(self):
        current_layout = _get_current_layout()
        if current_layout:
            current_layout.element.children.append(self.element)
            self._previous_layout = current_layout

        CurrentLayout.set(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        CurrentLayout.set(self._previous_layout)


class Element:
    SKIP_ID_TAGS: ClassVar[list[str]] = ["html", "head", "body", "script", "meta", "link", "title"]

    @staticmethod
    def _cls_to_class(**attrs):
        if "cls" in attrs:
            attrs["class"] = attrs.pop("cls")
        return attrs

    def __init__(self, tag: HTMLTag, **attrs):
        if "id" not in attrs and tag not in self.SKIP_ID_TAGS:
            attrs["id"] = f"schorle-{tag}-{id(self)}"

        self._layout = Layout(self)
        self._children = []
        self.tag = tag
        self.attrs = self._cls_to_class(**attrs)
        self._subscribers = []

    @property
    def children(self):
        return self._children

    @property
    def layout(self):
        return self._layout

    def add(self):
        current_layout = _get_current_layout()
        if current_layout:
            current_layout.element.children.append(self)
        else:
            raise RuntimeError("No current layout")

    def __repr__(self):
        return f"<{self.tag} {self.attrs}>"
