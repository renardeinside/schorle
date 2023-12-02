from contextvars import ContextVar
from typing import ClassVar, Optional

current_element: ContextVar[Optional["BaseElement"]] = ContextVar("current_element", default=None)
target_to_func: ContextVar[dict] = ContextVar("target_to_func", default={})


def get_current_element():
    try:
        return current_element.get()
    except LookupError:
        return None


def dynamic(func):
    element = get_current_element()
    if element:
        element.add(func)
    else:
        raise ValueError("dynamic can only be used within an element context")


class BaseElement:
    SKIP_TAGS: ClassVar[list[str]] = ["html", "head", "body", "script", "meta", "link", "title"]

    def __init__(self, tag, **attrs):
        if "id" not in attrs and tag not in self.SKIP_TAGS:
            attrs["id"] = f"schorle-{tag}-{id(self)}"
        if "cls" in attrs:
            attrs["class"] = attrs.pop("cls")

        self._children = []
        self.tag = tag
        self.attrs = attrs
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

    def __repr__(self):
        return f"<{self.tag} {self._children} {self.attrs}>"

    def traverse(self):
        yield self
        for child in self.children:
            yield child
            if isinstance(child, BaseElement):
                yield from child.traverse()


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
        mapper = target_to_func.get()
        mapper[self.attrs["id"]] = on_click
        target_to_func.set(mapper)

    @property
    def on_click(self):
        return self._on_click
