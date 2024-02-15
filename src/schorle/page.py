from abc import abstractmethod

from schorle.component import Component
from schorle.context_vars import RENDER_CONTROLLER
from schorle.tags import HTMLTag


class Page(Component):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    @abstractmethod
    def render(self):
        pass

    def __enter__(self):
        RENDER_CONTROLLER.get().in_page_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        RENDER_CONTROLLER.get().in_page_context = True
        pass
