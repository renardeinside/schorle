from __future__ import annotations

import inspect
from abc import abstractmethod
from copy import deepcopy
from typing import Any, Callable
from uuid import uuid4

from loguru import logger
from lxml import etree
from pydantic import Field

from schorle.prototypes import ElementPrototype, WithRender
from schorle.rendering_context import RENDERING_CONTEXT, rendering_context
from schorle.tags import HTMLTag


class Component(ElementPrototype, WithRender):
    tag: HTMLTag | str = HTMLTag.DIV

    def initialize(self, **kwargs):
        pass

    def __init__(self, **data):
        super().__init__(**data)

        if not self.element_id:
            self.element_id = f"sle-{str(uuid4())[0:8]}"
        self.initialize()

        self._append_to_context(strict=False)

    def _append_to_context(self, *, strict: bool = True):
        rc = RENDERING_CONTEXT.get()
        if strict and rc is None:
            raise RuntimeError("Component cannot be rendered outside of a RenderingContext")
        if rc is not None:
            RENDERING_CONTEXT.get().append(self)

    @abstractmethod
    def render(self, **kwargs):
        pass

    def render_in_context(self) -> ElementPrototype:
        self._cleanup()
        with rendering_context(root=self, session=self.session) as rc:
            self.render()
            return rc.root

    def __call__(self):
        self._append_to_context(strict=True)

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __str__(self):
        return self.__repr__()

    def to_string(self) -> str:
        self._cleanup()
        with rendering_context(root=self, session=self.session) as rc:
            self.render()
        return etree.tostring(rc.to_lxml(), pretty_print=True).decode("utf-8")

    async def rerender(self):
        if not self.session:
            logger.warning("No session provided for component")
        else:
            html = self.to_string()
            await self.session.morph(self.element_id, html)


class Injector:
    def __init__(self, signal):
        self.signal = signal

    @abstractmethod
    def inject(self, component: Component):
        pass


class Depends(Injector):

    @abstractmethod
    def inject(self, component: Component):
        value = deepcopy(self.signal)
        value.subscribe(component.rerender)
        return value


class DynamicComponent(Component):
    renderable: Callable
    kwargs: dict[str, Any] = Field(default_factory=dict)

    def initialize(self):
        params = inspect.signature(self.renderable).parameters
        for param_name, param in params.items():
            if isinstance(param.default, Injector):
                self.kwargs[param_name] = param.default.inject(self)

    def render(self):
        if self.kwargs:
            self.renderable(**self.kwargs)
        else:
            self.renderable()


class DynamicComponentFactory:
    def __init__(self, renderable: Callable, **kwargs):
        self.renderable = renderable
        self.kwargs = kwargs

    def __call__(self):
        return DynamicComponent(renderable=self.renderable, **self.kwargs)


def component(**kwargs) -> Callable[[Callable], DynamicComponentFactory]:
    def decorator(func) -> DynamicComponentFactory:
        c = DynamicComponentFactory(renderable=func, **kwargs)
        return c

    return decorator
