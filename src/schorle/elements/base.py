from contextvars import ContextVar
from typing import Optional

current_element: ContextVar[Optional["BaseElement"]] = ContextVar("current_element", default=None)


def get_current_element():
    try:
        return current_element.get()
    except LookupError:
        return None


class BaseElement:
    SKIP_TAGS = ["html", "head", "body", "script", "meta", "link", "title"]

    def __init__(self, tag, depends_on=None, **attrs):
        if "id" not in attrs and tag not in self.SKIP_TAGS:
            attrs["id"] = f"schorle-{tag}-{id(self)}"

        self._children = []
        self.tag = tag
        self.attrs = attrs
        self.depends_on = depends_on
        self.context = get_current_element()

        if not self.context:
            current_element.set(self)
        else:
            self.context.children.append(self)

    @property
    def children(self):
        return self._children

    def __enter__(self):
        current_element.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        current_element.set(self.context)

    def add(self, *children):
        self._children.extend(children)

    def clear(self):
        self._children = []

    def defer(self, *children):
        self.clear()
        self.add(*children)


class OnChangeElement(BaseElement):
    def __init__(self, tag, on_change=None, **kwargs):
        super().__init__(tag, **kwargs)
        self._on_change = on_change

    @property
    def on_change(self):
        return self._on_change


class OnClickElement(BaseElement):
    def __init__(self, tag, on_click=None, **kwargs):
        super().__init__(tag, **kwargs)
        self._on_click = on_click

    @property
    def on_click(self):
        return self._on_click
