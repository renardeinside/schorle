import asyncio
from typing import Callable, Optional

from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag


class Page(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    def find_by_id(self, element_id: str) -> Optional[Element]:
        for child in self.traverse():
            if child.element_id == element_id:
                return child
        return None

    def get_all_on_loads(self) -> list[Callable]:
        all_on_loads = self.get_on_loads()
        for element in self.traverse():
            all_on_loads.extend(element.get_on_loads())
        return all_on_loads

    def get_all_pre_render_tasks(self) -> list[asyncio.Task]:
        all_pre_renders = self.get_pre_renders()
        for element in self.traverse():
            all_pre_renders.extend(element.get_pre_renders())
        tasks = [asyncio.create_task(t()) for t in all_pre_renders]
        return tasks

    def subscribe_all_elements(self, subscriber):
        for element in self.traverse():
            element.subscribe(subscriber)

    def get_all_binding_tasks(self) -> list[asyncio.Task]:
        all_binds = self.get_binds()
        for element in self.traverse():
            all_binds.extend(element.get_binds())

        tasks = [asyncio.create_task(t()) for t in all_binds]
        return tasks
