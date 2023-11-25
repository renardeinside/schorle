from lxml.etree import Element


class BaseElement:
    def __init__(self, tag, children=None, **kwargs):
        self._element = Element(tag, **kwargs)
        self._children = [] if children is None else children

    def render(self):

        # Render children and append them to the current element
        # children can be either a string or a CustomElement
        for child in self._children:
            if isinstance(child, BaseElement):
                self._element.append(child.render())
            else:
                self._element.text = child

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


def p(*children, **attrs):
    return BaseElement('p', children=children, **attrs)


def Page(*children, **attrs):
    attrs["id"] = "schorle-page"
    return div(*children, **attrs)
