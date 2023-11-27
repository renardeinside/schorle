from typing import Iterator

from schorle.elements.base import BaseElement


class Page(BaseElement):
    def __init__(self, **attrs):
        attrs["id"] = "schorle-page"

        super().__init__("div", **attrs)

    def __call__(self, *args, **kwargs):
        return self

    def find_dependants_of(self, target_signal):
        """recursive search for elements that depend on a signal"""
        dependants = []
        for element in self._traverse(self):
            if isinstance(element, BaseElement) and element.depends_on:
                if target_signal in element.depends_on:
                    dependants.append(element)
        return dependants

    def _traverse(self, element) -> Iterator[BaseElement]:
        yield element
        for child in element.children:
            if isinstance(child, BaseElement):
                yield from self._traverse(child)

    def find_by_id(self, target_id) -> BaseElement | None:
        for element in self._traverse(self):
            if isinstance(element, BaseElement) and element.attrs.get("id") == target_id:
                return element
