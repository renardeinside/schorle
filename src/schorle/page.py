from schorle.elements.base import BaseElement


class Page(BaseElement):
    def __init__(self, *children, **attrs):
        attrs["id"] = "schorle-page"
        super().__init__("div", children=children, **attrs)

    def find_dependants_of(self, signal):
        """recursive search for elements that depend on a signal"""
        dependants = []
        for element in self._traverse(self):
            if isinstance(element, BaseElement) and element.depends_on:
                if signal in element.depends_on:
                    dependants.append(element)
        return dependants

    def _traverse(self, element):
        yield element
        for child in element.children:
            if isinstance(child, BaseElement):
                yield from self._traverse(child)
