from lxml.etree import Element

from schorle.signal import Signal


class BaseElement:
    def __init__(self, tag, children=None, depends_on=None, **kwargs):
        if 'id' not in kwargs and tag not in ['html', 'head', 'body', 'meta', 'title', 'link', 'script']:
            kwargs['id'] = f"schorle-{tag}-{id(self)}"
        self._element = Element(tag, **kwargs)
        self._children = [] if children is None else children
        self.depends_on = depends_on

    @property
    def children(self):
        return self._children

    @property
    def element(self):
        return self._element

    def find_by_id(self, target_id):

        if 'id' in self._element.attrib and self._element.attrib['id'] == target_id:
            return self

        for child in self._children:
            if isinstance(child, BaseElement):
                result = child.find_by_id(target_id)
                if result:
                    return result


class OnChangeElement(BaseElement):
    def __init__(self, tag, children=None, on_change=None, **kwargs):
        super().__init__(tag, children, **kwargs)
        self._on_change = on_change

    @property
    def on_change(self):
        return self._on_change


class OnClickElement(BaseElement):
    def __init__(self, tag, children=None, on_click=None, **kwargs):
        super().__init__(tag, children, **kwargs)
        self._on_click = on_click

    @property
    def on_click(self):
        return self._on_click


# Custom functions for each HTML element
def div(*children, **attrs):
    return BaseElement('div', children=children, **attrs)


def input_(input_type: str, on_change, **attrs):
    attrs["type"] = input_type
    return OnChangeElement('input', children=None, on_change=on_change, **attrs)


def head(*children, **attrs):
    return BaseElement('head', children=children, **attrs)


def html(*children, **attrs):
    return BaseElement('html', children=children, **attrs)


def link(**attrs):
    return BaseElement('link', children=None, **attrs)


def meta(**attrs):
    return BaseElement('meta', children=None, **attrs)


def script(**attrs):
    return BaseElement('script', children=[""], **attrs)


def title(*children, **attrs):
    return BaseElement('title', children=children, **attrs)


def body(*children, **attrs):
    return BaseElement('body', children=children, **attrs)


def p(*children, depends_on, **attrs):
    return BaseElement('p', children=children, depends_on=depends_on, **attrs)


def button(*children, on_click, **attrs):
    return OnClickElement('button', children=children, on_click=on_click, **attrs)


class Page(BaseElement):
    def __init__(self, *children, **attrs):
        attrs["id"] = "schorle-page"
        super().__init__('div', children=children, **attrs)

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


class fmt:
    def __init__(self, fmt_string, *args):
        self.fmt_string = fmt_string
        self.args = args

    def __str__(self):
        return self.fmt_string.format(*self.args)


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
