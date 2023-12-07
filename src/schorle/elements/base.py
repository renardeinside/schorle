from contextvars import ContextVar
from typing import Callable, ClassVar

from loguru import logger

from schorle.reactive import Reactive

onclick_mapper: ContextVar[dict[str, Callable]] = ContextVar("onclick_mapper", default={})


class BaseElement:
    SKIP_TAGS: ClassVar[list[str]] = ["html", "head", "body", "script", "meta", "link", "title"]

    @staticmethod
    def _cls_to_class(**attrs):
        if "cls" in attrs:
            attrs["class"] = attrs.pop("cls")
        return attrs

    def __init__(self, tag, **attrs):
        if "id" not in attrs and tag not in self.SKIP_TAGS:
            attrs["id"] = f"schorle-{tag}-{id(self)}"
        self._children = []
        self.tag = tag
        self.attrs = self._cls_to_class(**attrs)
        self._subscribers = []

    @property
    def children(self):
        return self._children

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        # current_element.set(self.context)

    def add(self, *children):
        self._children.extend(children)

    def __repr__(self):
        return f"<{self.tag} {self._children} {self.attrs}>"

    def subscribe(self, callback: Callable):
        self._subscribers.append(callback)

    def traverse(self):
        yield self
        for child in self.children:
            yield child
            if isinstance(child, BaseElement):
                yield from child.traverse()

    async def update(self, *children, **attrs):
        logger.info(f"Updating {self} with {children} and {attrs}")

        if children:
            self._children = []
            self.add(*children)

        if attrs:
            new_attrs = self._cls_to_class(**attrs)
            self.attrs.update(new_attrs)

        logger.info(f"Notifying subscribers {self._subscribers}")
        for sub in self._subscribers:
            await sub(self)


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
        onclick_mapper.get()[self.attrs["id"]] = on_click

    @property
    def on_click(self):
        return self._on_click


class InputElement(BaseElement):
    def __init__(self, bind: Reactive, **kwargs):
        super().__init__("input", **kwargs)
        self.bind = bind
        self.attrs["schorle-bind"] = bind.reactive_id
