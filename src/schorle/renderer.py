from lxml.etree import Element, tostring

from schorle.elements.base import BaseElement
from schorle.signal import Signal


class Renderer:
    @classmethod
    def _render(cls, base_element: BaseElement) -> Element:
        element = Element(base_element.tag, **base_element.attrs)
        for child in base_element.children:
            if isinstance(child, BaseElement):
                element.append(cls._render(child))
            elif isinstance(child, Signal):
                element.text = str(child.value)
            else:
                element.text = str(child)
        return element

    @classmethod
    def render(cls, base_element: BaseElement) -> str:
        return tostring(cls._render(base_element), pretty_print=True).decode("utf-8")
