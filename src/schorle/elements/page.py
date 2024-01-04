from typing import Optional

from schorle.elements.base import Element
from schorle.elements.tags import HTMLTag


class Page(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    def find_by_id(self, element_id: str) -> Optional[Element]:
        for child in self.traverse_elements(nested=True):
            if child.element_id == element_id:
                return child
        return None

    def get_binding_tasks(self) -> list:
        return self._binding_tasks
