from lxml.etree import Element

from schorle.elements.base import BaseElement
from schorle.signal import Signal


class Renderer:
    @staticmethod
    def render(base_element: BaseElement) -> Element:
        element = Element(base_element.element.tag, **base_element.element.attrib)
        for child in base_element.children:
            if isinstance(child, BaseElement):
                element.append(Renderer.render(child))
            elif isinstance(child, Signal):
                element.text = str(child.value)
            else:
                element.text = str(child)
        return element
