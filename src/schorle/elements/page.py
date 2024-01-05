from typing import Optional

from schorle.elements.base import Element, Subscriber
from schorle.elements.tags import HTMLTag


class Page(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    def find_by_id(self, element_id: str) -> Optional[Element]:
        for child in self.traverse_elements(nested=True):
            if child.element_id == element_id:
                return child
        return None

    def subscribe_to_all(self, subscriber: Subscriber) -> None:
        """
        Subscribe to the page and all its children.
        """
        self.subscribe(subscriber)
        for child in self.traverse_elements(nested=True):
            child.subscribe(subscriber)
