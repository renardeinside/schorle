from __future__ import annotations

from collections.abc import Iterator

from loguru import logger
from lxml.etree import Element as LxmlElementFactory
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import ConfigDict, Field, PrivateAttr

from schorle.elements.base.mixins import AttrsMixin, FactoryMixin
from schorle.elements.tags import HTMLTag
from schorle.reactives.base import ReactiveBase
from schorle.reactives.text import Text


class BaseElement(AttrsMixin, FactoryMixin):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    tag: HTMLTag
    text: Text | str = Field(default=Text(), description="Text content of the element, if any")
    style: dict[str, str] | None = Field(default=None, description="Style attributes of the element, if any")
    element_id: str | None = Field(default=None, description="Explicitly set the id of the element, if required")
    _rendering_element: LxmlElement | None = PrivateAttr(default=None)
    render_behaviour: str = Field(default="default", description="Render behaviour of the element")

    def walk(self, parent: BaseElement | None = None) -> Iterator[tuple[BaseElement | None, BaseElement]]:
        """
        Traverse the element tree and yield a tuple of [parent, child] elements.
        """
        yield parent, self
        for field_name, field_info in self.model_fields.items():
            if field_info.json_schema_extra and field_info.json_schema_extra.get("page_reference"):
                continue
            else:
                element = getattr(self, field_name)
                if isinstance(element, BaseElement):
                    yield from element.walk(self)
                elif isinstance(element, ReactiveBase):
                    value = element.get()
                    if isinstance(value, list):
                        for _element in value:
                            if isinstance(_element, BaseElement):
                                yield from _element.walk(self)
                    elif isinstance(value, BaseElement):
                        yield from value.walk(self)
                elif isinstance(element, list):
                    for _element in element:
                        if isinstance(_element, BaseElement):
                            yield from _element.walk(self)

    def traverse(self, *, skip_self: bool = False) -> Iterator[BaseElement]:
        """
        Traverse the element tree and yield each element.
        """
        if not skip_self:
            yield self
        for field_name, field_info in self.model_fields.items():
            if field_info.json_schema_extra and field_info.json_schema_extra.get("page_reference"):
                continue
            else:
                element = getattr(self, field_name)
                if isinstance(element, BaseElement):
                    yield from element.traverse()
                elif isinstance(element, ReactiveBase):
                    value = element.get()
                    if isinstance(value, list):
                        for _element in value:
                            if isinstance(_element, BaseElement):
                                yield from _element.traverse()
                    elif isinstance(value, BaseElement):
                        yield from value.traverse()
                elif isinstance(element, list):
                    for _element in element:
                        if isinstance(_element, BaseElement):
                            yield from _element.traverse()

    def _add_classes(self, element: LxmlElement):
        pass

    def get_prerender(self) -> LxmlElement:
        if self._rendering_element is None:
            element = LxmlElementFactory(self.tag.value)

            if self.element_id is not None:
                element.set("id", self.element_id)

            if self.style is not None:
                element.set("style", ";".join([f"{k}:{v}" for k, v in self.style.items()]))

            self._add_classes(element)

            for k, v in self.get_element_attributes().items():
                if v is not None:
                    element.set(k, v)
            if self.text is not None:
                _text = self.text.get() if isinstance(self.text, Text) else self.text
                element.text = _text
            self._rendering_element = element

        return self._rendering_element

    def _render(self) -> LxmlElement:
        root_element = None
        for parent, child in self.walk():
            if not parent:
                root_element = child.get_prerender()
            elif parent.render_behaviour == "default" and child.render_behaviour == "default":
                # default behaviour is to append the child to the parent
                parent.get_prerender().append(child.get_prerender())
            elif parent.render_behaviour == "flatten" and child.render_behaviour == "default":
                # flatten behaviour is to append the children of the child to the parent
                for sub_children in child.traverse(skip_self=True):
                    parent.get_prerender().append(sub_children.get_prerender())
            elif parent.render_behaviour == "default" and child.render_behaviour == "flatten":
                # flatten behaviour is to append the children of the child to the parent
                for sub_children in child.traverse(skip_self=True):
                    parent.get_prerender().append(sub_children.get_prerender())
            elif parent.render_behaviour == "flatten" and child.render_behaviour == "flatten":
                # in this case we need to get the parent of the parent and append the children of the child to it
                # this is because we need to flatten the children of the child to the parent of the parent
                parent_of_parent = parent.get_prerender().getparent()
                if parent_of_parent is not None:
                    for sub_children in child.traverse(skip_self=True):
                        parent_of_parent.append(sub_children.get_prerender())
                else:
                    logger.warning("Failed to get parent of parent")

        if root_element is None:
            msg = f"Failed to render element {self}."
            raise RuntimeError(msg)

        for element in self.traverse():
            element._rendering_element = None
        return root_element

    def render(self) -> str:
        return self._lxml_to_string(self._render())

    def __repr__(self):
        return f"<{self.tag} {self.element_id}>"

    def __str__(self):
        return self.__repr__()

    def _lxml_to_string(self, element: LxmlElement) -> str:
        _result = tostring(element, pretty_print=True, with_comments=True).decode("utf-8")
        return _result
