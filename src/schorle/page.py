from typing import Iterator, Literal, Optional

from schorle.elements.base import BaseElement

Theme = Literal[
    "light",
    "dark",
    "cupcake",
    "bumblebee",
    "emerald",
    "corporate",
    "synthwave",
    "retro",
    "cyberpunk",
    "valentine",
    "halloween",
    "garden",
    "forest",
    "aqua",
    "lofi",
    "pastel",
    "fantasy",
    "wireframe",
    "black",
    "luxury",
    "dracula",
    "cmyk",
    "autumn",
    "business",
    "acid",
    "lemonade",
    "night",
    "coffee",
    "winter",
    "dim",
    "nord",
    "sunset",
]


class Page(BaseElement):
    def __init__(self, theme: Optional[Theme] = None, **attrs):
        attrs["id"] = "schorle-page"

        if theme:
            attrs["data-theme"] = theme

        super().__init__("div", **attrs)

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
