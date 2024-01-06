import asyncio
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

    def get_all_on_load_tasks(self) -> list[asyncio.Task]:
        all_on_loads = self.get_on_loads()
        for element in self.traverse_elements(nested=True):
            all_on_loads.extend(element.get_on_loads())

        tasks = [asyncio.create_task(t()) for t in all_on_loads]
        return tasks

    def subscribe_all_elements(self, subscriber):
        self.subscribe(subscriber)
        for child in self.traverse_elements(nested=True):
            child.subscribe(subscriber)

    def get_all_binding_tasks(self) -> list[asyncio.Task]:
        all_binds = self.get_binds()
        for element in self.traverse_elements(nested=True):
            all_binds.extend(element.get_binds())

        tasks = [asyncio.create_task(t()) for t in all_binds]
        return tasks
