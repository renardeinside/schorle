from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar

from loguru import logger
from lxml import etree

from schorle.attrs import On
from schorle.prototypes import ElementPrototype, WithRender
from schorle.session import Session
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
        self.root: ElementPrototype = ElementPrototype(tag="root") if root is None else root
        self.current_parent = self.root

    def append(self, element: ElementPrototype):
        self.current_parent.append(element)

    def become_parent(self, element: ElementPrototype):
        element.set_parent(self.current_parent)
        self.current_parent = element

    def reset_parent(self):
        self.current_parent = self.current_parent.get_parent()

    def set_text(self, text_value: str):
        self.current_parent.set_text(text_value)

    def covert_proto_to_lxml(self, proto: ElementPrototype, session: Session | None) -> LXMLElement:
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

        if session:
            proto.session = session

            handlers = []

            if proto.on:
                _ons = [proto.on] if isinstance(proto.on, On) else proto.on
                for on in _ons:
                    handler_uuid = session.register_handler(proto.on.handler)
                    handlers.append({"event": on.event, "handler": handler_uuid})

            if proto.bind:

                async def _handler(new_value: str):
                    await proto.bind.reactive.set(new_value)

                lxml_element.set(proto.bind.property, proto.bind.reactive.rx)
                _on = On(event="input", handler=_handler)
                handler_uuid = session.register_handler(_handler)
                handlers.append({"event": _on.event, "handler": handler_uuid})

            if handlers:
                lxml_element.set("sle-on", json.dumps(handlers))
        else:
            logger.warning(f"No session found for proto: {proto}")

        if proto.style:
            lxml_element.set("style", ";".join([f"{key}: {value}" for key, value in proto.style.items()]))

        for child in proto.get_children():
            if isinstance(child, WithRender):
                rendered = child.render_in_context()
                lxml_child = self.covert_proto_to_lxml(rendered, session)
            else:
                lxml_child = self.covert_proto_to_lxml(child, session)
            lxml_element.append(lxml_child)

        fix_self_closing_tags(lxml_element)
        return lxml_element

    def to_lxml(self, session: Session | None = None):
        return self.covert_proto_to_lxml(self.root, session)


RENDERING_CONTEXT: ContextVar[RenderingContext | None] = ContextVar("rendering_context", default=None)
