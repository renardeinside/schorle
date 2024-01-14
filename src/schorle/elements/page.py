from typing import Optional

from schorle.elements.base.base import BaseElement
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag
from schorle.state import State


class Page(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"
    state: State | None = None

    def find_by_id(self, element_id: str) -> Optional[BaseElement]:
        for child in self.traverse():
            if child.element_id == element_id:
                return child
        return None
