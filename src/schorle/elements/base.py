from lxml.etree import Element


class BaseElement:
    def __init__(self, tag, children=None, depends_on=None, **kwargs):
        if "id" not in kwargs and tag not in ["html", "head", "body", "meta", "title", "link", "script"]:
            kwargs["id"] = f"schorle-{tag}-{id(self)}"
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
        if "id" in self._element.attrib and self._element.attrib["id"] == target_id:
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
