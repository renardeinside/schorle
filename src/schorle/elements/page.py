from typing import Optional

from pydantic import Field

from schorle.elements.base.base import BaseElement
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag


class Page(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    def find_by_id(self, element_id: str) -> Optional[BaseElement]:
        for child in self.traverse():
            if child.element_id == element_id:
                return child
        return None

    async def execute_all_before_render(self):
        self.inject_page_reference(self)

        for element in self.traverse():
            if isinstance(element, Element):
                await element.before_render()
                # cleanup render queues
                for attr in element.get_reactive_attributes():
                    while not attr._render_queue.empty():
                        await attr._render_queue.get()

        self.inject_page_reference(self)


def PageReference():  # noqa: N802
    return Field(None, json_schema_extra={"attribute": False, "page_reference": True})
