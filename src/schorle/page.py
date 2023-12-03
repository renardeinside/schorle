from schorle.elements.base import BaseElement


class Page(BaseElement):
    def __init__(self, cls=None, **attrs):
        attrs["id"] = "schorle-page"
        attrs["class"] = cls
        super().__init__("div", **attrs)
