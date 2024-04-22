from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from lxml import etree

from schorle.prototypes import ElementPrototype
from schorle.tags import HTMLTag
from schorle.types import LXMLElement
from schorle.utils import fix_self_closing_tags


@contextmanager
def rendering_context(root: ElementPrototype | None = None):
    rc = RenderingContext(root=root)
    _token = RENDERING_CONTEXT.set(rc)
    yield rc
    RENDERING_CONTEXT.reset(_token)


class RenderingContext:
    def __init__(self, root: ElementPrototype | None = None):
        self.root = ElementPrototype(tag="root") if root is None else root
        self.current_parent = self.root
        self.previous_parent = None
        self.pre_previous_parent = None

    def append(self, element: ElementPrototype):
        self.current_parent.append(element)

    def become_parent(self, element: ElementPrototype):
        self.pre_previous_parent = self.previous_parent
        self.previous_parent = self.current_parent
        self.current_parent = element

    def reset_parent(self):
        self.current_parent = self.previous_parent
        self.previous_parent = self.pre_previous_parent

    def set_text(self, text_value: str):
        self.current_parent.set_text(text_value)

    def covert_proto_to_lxml(self, proto: ElementPrototype) -> LXMLElement:
        lxml_element = etree.Element(proto.tag.value if isinstance(proto.tag, HTMLTag) else proto.tag)

        if proto.element_id:
            lxml_element.set("id", proto.element_id)

        if proto._text:
            lxml_element.text = proto._text

        if proto.attrs:
            for key, value in proto.attrs.items():
                _key = "class" if key == "classes" else key
                lxml_element.set(_key, value)

        if proto.classes:
            if isinstance(proto.classes, str):
                proto.classes = [proto.classes]
            lxml_element.set("class", " ".join(proto.classes))

        if proto.style:
            lxml_element.set("style", ";".join([f"{key}: {value}" for key, value in proto.style.items()]))

        for child in proto.get_children():
            if hasattr(child, "_render"):
                rendered = child._render()
                lxml_child = self.covert_proto_to_lxml(rendered)
            else:
                lxml_child = self.covert_proto_to_lxml(child)
            lxml_element.append(lxml_child)

        fix_self_closing_tags(lxml_element)
        return lxml_element

    def to_lxml(self):
        return self.covert_proto_to_lxml(self.root)


RENDERING_CONTEXT: ContextVar[RenderingContext | None] = ContextVar("rendering_context", default=None)
