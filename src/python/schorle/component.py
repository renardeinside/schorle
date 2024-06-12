from __future__ import annotations

import inspect
from abc import abstractmethod
from functools import partial
from typing import Callable, ParamSpec, TypeVar
from uuid import uuid4

from loguru import logger
from lxml import etree

from schorle.prototypes import ElementPrototype
from schorle.rendering_context import RENDERING_CONTEXT, RenderingContext, rendering_context
from schorle.store import Marker
from schorle.tags import HTMLTag


class Component(ElementPrototype):
    tag: HTMLTag | str = HTMLTag.DIV

    def initialize(self, **kwargs):
        pass

    def initialize_with_session(self):
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

    def render_in_context(self) -> RenderingContext:
        self._cleanup()
        if self.session:
            self.initialize_with_session()
        else:
            logger.warning("No session provided for component")
        with rendering_context(root=self, session=self.session) as rc:
            self.render()
            return rc

    def __call__(self):
        self._append_to_context(strict=True)

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __str__(self):
        return self.__repr__()

    def to_string(self) -> str:
        rc = self.render_in_context()
        return etree.tostring(rc.to_lxml(), pretty_print=True).decode("utf-8")

    async def rerender(self):
        if not self.session:
            logger.warning("No session provided for component")
        else:
            html = self.to_string()
            await self.session.morph(self.element_id, html)


class DynamicComponent(Component):
    renderable: Callable
    render_kwargs: dict | None = None

    def initialize(self):
        if not self.element_id:
            self.element_id = f"sle-{str(uuid4())[0:8]}"

    def initialize_with_session(self):
        signature = inspect.signature(self.renderable)
        params = signature.parameters
        collected = {}
        for name, param in params.items():
            if isinstance(param.default, Marker):
                marker: Marker = param.default
                signal = marker.get_instance(self.session)
                collected[name] = signal
                if marker.marker_type == "depends":
                    signal.subscribe(self.rerender)

        self.renderable = partial(self.renderable, **collected)

        if self.render_kwargs:
            self.renderable = partial(self.renderable, **self.render_kwargs)

    def render(self):
        self.renderable()


P = ParamSpec("P")
T = TypeVar("T")


class DynamicComponentFactory:
    def __init__(self, renderable: Callable[P, T], **kwargs):
        self.renderable = renderable
        self.kwargs = kwargs

    def __call__(self, **kwargs: P.kwargs):
        return DynamicComponent(renderable=self.renderable, render_kwargs=kwargs, **self.kwargs)


def component(
    **kwargs,
) -> Callable[P, DynamicComponentFactory]:
    def wrapper(renderable: Callable[P, T]) -> DynamicComponentFactory:
        return DynamicComponentFactory(renderable, **kwargs)

    return wrapper
