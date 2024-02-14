from abc import abstractmethod

from schorle.component import Component
from schorle.tags import HTMLTag


class Page(Component):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    @abstractmethod
    def render(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
