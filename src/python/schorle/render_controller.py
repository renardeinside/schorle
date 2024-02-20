import contextvars
from typing import Any

from lxml import etree

from schorle.types import LXMLElement


class RenderController:
    def __init__(self, page: Any | None = None):
        self._root: LXMLElement = etree.Element("root")
        self.previous: LXMLElement = self._root
        self.current: LXMLElement = self._root
        self.page: Any | None = page
        self.component_root: LXMLElement | None = None

    def get_root(self) -> LXMLElement:
        return self._root


class RenderControllerMixin:
    @property
    def controller(self) -> RenderController:
        return RENDER_CONTROLLER.get()


RENDER_CONTROLLER: contextvars.ContextVar[RenderController] = contextvars.ContextVar(
    "render_controller", default=RenderController()
)
