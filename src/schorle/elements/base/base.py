from __future__ import annotations

from inspect import isclass
from types import GenericAlias, UnionType
from typing import Any, Iterator, get_origin

from loguru import logger
from lxml.etree import Element as LxmlElementFactory
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import ConfigDict, Field, PrivateAttr
from pydantic.fields import FieldInfo

from schorle.elements.base.mixins import AttrsMixin, FactoryMixin
from schorle.elements.tags import HTMLTag
from schorle.reactives.base import ReactiveBase
from schorle.reactives.classes import Classes
from schorle.reactives.text import Text


class BaseElement(AttrsMixin, FactoryMixin):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    tag: HTMLTag
    text: Text | str = Field(default=Text(), description="Text content of the element, if any")
    style: dict[str, str] | None = Field(default=None, description="Style attributes of the element, if any")
    element_id: str | None = Field(default=None, description="Explicitly set the id of the element, if required")
    _rendering_element: LxmlElement | None = PrivateAttr(default=None)
    render_behaviour: str = Field(default="default", description="Render behaviour of the element")

    def _union_related_to_element(self, anno: UnionType):
        for arg in anno.__args__:
            if isclass(arg) and get_origin(arg) not in [list, dict] and issubclass(arg, BaseElement):
                return True
            elif isinstance(arg, UnionType):
                return self._union_related_to_element(arg)

    def _list_or_dict_related_to_element(self, anno: GenericAlias):
        for arg in anno.__args__:
            if isclass(arg) and issubclass(arg, BaseElement):
                return True
            elif isinstance(arg, UnionType):
                return self._union_related_to_element(arg)

    def _related_to_element(self, field: FieldInfo) -> bool:
        anno: type[Any] | None = field.annotation
        if get_origin(anno) in [list, dict] and type(anno) is GenericAlias:
            return self._list_or_dict_related_to_element(anno)  # type: ignore[arg-type]
        if isclass(anno) and issubclass(anno, BaseElement):
            return True
        elif isinstance(anno, UnionType) and self._union_related_to_element(anno):
            return True
        elif isclass(anno) and issubclass(anno, ReactiveBase) and not issubclass(anno, (Text, Classes)):
            return True
        else:
            return False

    def walk(self, parent: BaseElement | None = None) -> Iterator[tuple[BaseElement | None, BaseElement]]:
        """
        Traverse the element tree and yield a tuple of [parent, child] elements.
        """
        yield parent, self
        for k, v in self.model_fields.items():
            if v.json_schema_extra and v.json_schema_extra.get("page_reference"):
                continue
            elif self._related_to_element(v):
                element = getattr(self, k)
                if isinstance(element, BaseElement):
                    yield from element.walk(self)
                elif isinstance(element, ReactiveBase):
                    value = element.get()
                    if isinstance(value, list):
                        for _element in value:
                            yield from _element.walk(self)
                    elif isinstance(value, BaseElement):
                        yield from value.walk(self)
                elif isinstance(element, list):
                    for _element in element:
                        yield from _element.walk(self)

    def traverse(self, *, skip_self: bool = False) -> Iterator[BaseElement]:
        """
        Traverse the element tree and yield each element.
        """
        if not skip_self:
            yield self
        for k, v in self.model_fields.items():
            if v.json_schema_extra and v.json_schema_extra.get("page_reference"):
                continue
            elif self._related_to_element(v):
                element = getattr(self, k)
                if isinstance(element, BaseElement):
                    yield from element.traverse()
                elif isinstance(element, ReactiveBase):
                    value = element.get()
                    if isinstance(value, list):
                        for _element in value:
                            yield from _element.traverse()
                    elif isinstance(value, BaseElement):
                        yield from value.traverse()
                elif isinstance(element, list):
                    for _element in element:
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
                element.text = self.text.get() if isinstance(self.text, Text) else self.text
            self._rendering_element = element

        return self._rendering_element

    def render(self) -> str:
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

        result = tostring(root_element, pretty_print=True).decode("utf-8")
        for element in self.traverse():
            element._rendering_element = None
        return result

    def __repr__(self):
        return f"<{self.tag} {self.element_id}>"

    def __str__(self):
        return self.__repr__()
