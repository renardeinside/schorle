from abc import abstractmethod
from asyncio import Queue
from typing import Any

from pydantic import Field, PrivateAttr

from schorle.component import Component
from schorle.tags import HTMLTag


class Page(Component):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"
    reactives: dict[str, Any] = Field(default_factory=dict)
    _render_queue: Queue[Component] = PrivateAttr(default_factory=Queue)

    def append_to_queue(self, component: Component):
        self._render_queue.put_nowait(component)

    @abstractmethod
    def render(self):
        pass

    def __enter__(self):
        self.controller.page = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.controller.page = None
        pass
