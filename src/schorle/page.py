from schorle.elements.base import Element


class Page(Element):
    def __init__(self, cls=None, **attrs):
        attrs["id"] = "schorle-page"
        attrs["class"] = cls
        super().__init__("div", **attrs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
