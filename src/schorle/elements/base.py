from collections import deque

SKIP_ID_TAGS = ["html", "head", "body", "meta", "title", "link", "script"]

CONTEXT = deque()


class BaseElement:
    def __init__(self, tag, depends_on=None, **attrs):
        if "id" not in attrs and tag not in SKIP_ID_TAGS:
            attrs["id"] = f"schorle-{tag}-{id(self)}"

        self.tag = tag
        self.children = []

        self.depends_on = depends_on
        self.attrs = attrs

        if CONTEXT:
            CONTEXT[-1].add(self)

    def __enter__(self):
        CONTEXT.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        CONTEXT.pop()

    def add(self, *elements):
        self.children.extend(list(elements))


class OnChangeElement(BaseElement):
    def __init__(self, tag, children=None, on_change=None, **kwargs):
        super().__init__(tag, children, **kwargs)
        self._on_change = on_change

    @property
    def on_change(self):
        return self._on_change


class OnClickElement(BaseElement):
    def __init__(self, tag, on_click=None, **kwargs):
        super().__init__(tag, **kwargs)
        self._on_click = on_click

    @property
    def on_click(self):
        return self._on_click
