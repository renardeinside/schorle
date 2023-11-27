SKIP_ID_TAGS = ["html", "head", "body", "meta", "title", "link", "script"]

CONTEXT = {}


class BaseElement:
    def __init__(self, tag, children=None, depends_on=None, **attrs):
        if "id" not in attrs and tag not in SKIP_ID_TAGS:
            attrs["id"] = f"schorle-{tag}-{id(self)}"

        self.tag = tag
        self.children = [] if children is None else list(children)
        self.depends_on = depends_on
        self.attrs = attrs

        if CONTEXT.get("current_element"):
            CONTEXT["current_element"].children.append(self)

    def __enter__(self):
        CONTEXT["previous_element"] = CONTEXT.get("current_element")
        CONTEXT["current_element"] = self
        if self.children:
            msg = f"{self.tag} cannot be used with children when used as a context."
            raise ValueError(msg)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        CONTEXT["current_element"] = CONTEXT.get("previous_element")
        CONTEXT["previous_element"] = None


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
