from __future__ import annotations

from abc import abstractmethod
from uuid import uuid4

from lxml import etree

from schorle.prototypes import ElementPrototype
from schorle.rendering_context import RENDERING_CONTEXT, rendering_context
from schorle.tags import HTMLTag


class Component(ElementPrototype):
    tag: HTMLTag | str = HTMLTag.SCHORLE_COMPONENT

    def initialize(self):
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
    def render(self):
        pass

    def _render(self):
        self._cleanup()
        with rendering_context(root=self) as rc:
            self.render()
            return rc.root

    def __call__(self):
        self._append_to_context(strict=True)

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __str__(self):
        return self.__repr__()

    def to_string(self) -> str:
        with rendering_context(root=self) as rc:
            self.render()
        return etree.tostring(rc.to_lxml(), pretty_print=True).decode("utf-8")
