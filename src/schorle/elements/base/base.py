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

from schorle.elements.base.mixins import AttrsMixin, InjectableMixin
from schorle.elements.tags import HTMLTag


class BaseElement(AttrsMixin, InjectableMixin):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    tag: HTMLTag
    text: str | None = Field(default=None, description="Text content of the element, if any")
    style: dict[str, str] | None = Field(default=None, description="Style attributes of the element, if any")
    element_id: str | None = Field(default=None, description="Explicitly set the id of the element, if required")
    _rendering_element: LxmlElement | None = PrivateAttr(default=None)

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
        else:
            return False

    def walk(self, parent: BaseElement | None = None) -> Iterator[tuple[BaseElement | None, BaseElement]]:
        """
        Traverse the element tree and yield a tuple of [parent, child] elements.
        """
        yield parent, self
        for k, v in self.model_fields.items():
            if self._related_to_element(v):
                element = getattr(self, k)
                if isinstance(element, BaseElement):
                    yield from element.walk(self)
                elif isinstance(element, list):
                    for _element in element:
                        yield from _element.walk(self)

    def traverse(self) -> Iterator[BaseElement]:
        """
        Traverse the element tree and yield each element.
        """
        yield self
        for k, v in self.model_fields.items():
            if self._related_to_element(v):
                element = getattr(self, k)
                if isinstance(element, BaseElement):
                    yield from element.traverse()
                elif isinstance(element, list):
                    for _element in element:
                        yield from _element.traverse()

    def _add_classes(self, element: LxmlElement):
        pass

    def get_element(self) -> LxmlElement:
        if self._rendering_element is None:
            element = LxmlElementFactory(self.tag.value)

            if self.element_id is not None:
                element.set("id", self.element_id)

            if self.style is not None:
                element.set("style", ";".join([f"{k}:{v}" for k, v in self.style.items()]))

            self._add_classes(element)

            for k, v in self.attrs.items():
                if v is not None:
                    element.set(k, v)
            if self.text is not None:
                element.text = self.text
            self._rendering_element = element

        return self._rendering_element

    def render(self) -> str:
        logger.info(f"Rendering element {self}")

        root_element = None
        for parent, child in self.walk():
            if not parent:
                root_element = child.get_element()
            else:
                parent.get_element().append(child.get_element())
        if root_element is None:
            msg = f"Failed to render element {self}."
            raise RuntimeError(msg)

        result = tostring(root_element, pretty_print=True).decode("utf-8")
        logger.debug(f"Rendered element {self} to {result}")
        for element in self.traverse():
            element._rendering_element = None
        return result

    def __repr__(self):
        return f"<{self.tag} {self.element_id}>"

    def __str__(self):
        return self.__repr__()
