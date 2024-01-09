from __future__ import annotations

from functools import partial
from inspect import isclass
from types import GenericAlias, UnionType
from typing import Annotated, Iterator, get_origin

from loguru import logger
from lxml.etree import Element as LxmlElementFactory
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import ConfigDict, Field, PrivateAttr
from pydantic.fields import FieldInfo

from schorle.elements.attribute import Attribute
from schorle.elements.base.mixins import AttrsMixin, BindableMixin
from schorle.elements.classes import Classes
from schorle.elements.tags import HTMLTag
from schorle.observable import ObservableModel


class ObservableElement(ObservableModel):
    _selected_fields: list[str] = PrivateAttr(default=["text", "style", "classes", "element_id", "_trigger"])
    _trigger: str | None = PrivateAttr(default=None)

    def update(self):
        """
        Explicitly update the element.
        :return:
        """
        self._trigger = str(id(self))


class Element(ObservableElement, AttrsMixin, BindableMixin):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    tag: HTMLTag
    text: str | None = Field(default=None, description="Text content of the element, if any")
    style: dict[str, str] | None = Field(default=None, description="Style attributes of the element, if any")
    element_id: str | None = Field(default=None, description="Explicitly set the id of the element, if required")
    _rendering_element: LxmlElement | None = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)

    @classmethod
    def provide(cls, *args, **kwargs) -> type[Element]:
        return Annotated[cls, Field(default_factory=partial(cls, *args, **kwargs))]

    def _union_related_to_element(self, anno: UnionType):
        for arg in anno.__args__:
            if isclass(arg) and get_origin(arg) not in [list, dict] and issubclass(arg, Element):
                return True
            elif isinstance(arg, UnionType):
                return self._check_annotation_args(arg)

    def _list_or_dict_related_to_element(self, anno: GenericAlias):
        for arg in anno.__args__:
            if isclass(arg) and issubclass(arg, Element):
                return True
            elif isinstance(arg, UnionType):
                return self._check_annotation_args(arg)

    def _related_to_element(self, field: FieldInfo) -> bool:
        anno: UnionType | GenericAlias | type = field.annotation
        if get_origin(anno) in [list, dict]:
            return self._list_or_dict_related_to_element(anno)
        if isclass(anno) and issubclass(anno, Element):
            return True
        elif isinstance(anno, UnionType) and self._union_related_to_element(anno):
            return True

    def walk(self, parent: Element | None = None) -> Iterator[tuple[Element | None, Element]]:
        """
        Traverse the element tree and yield a tuple of [parent, child] elements.
        """
        yield parent, self
        for k, v in self.model_fields.items():
            if self._related_to_element(v):
                element = getattr(self, k)
                if isinstance(element, Element):
                    yield from element.walk(self)
                elif isinstance(element, list):
                    for _element in element:
                        yield from _element.walk(self)

    def traverse(self) -> Iterator[Element]:
        """
        Traverse the element tree and yield each element.
        """
        yield self
        for k, v in self.model_fields.items():
            if self._related_to_element(v):
                element = getattr(self, k)
                if isinstance(element, Element):
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
        result = tostring(root_element, pretty_print=True).decode("utf-8")
        logger.debug(f"Rendered element {self} to {result}")
        for element in self.traverse():
            element._rendering_element = None
        return result

    def __repr__(self):
        return f"<{self.tag} {self.element_id}>"

    def __str__(self):
        return self.__repr__()

    def update_text(self, text: str):
        self.text = text


class ElementWithGeneratedId(Element):
    hx_swap: str = Attribute(default="morph", alias="hx-swap-oob")
    _base_classes: Classes = PrivateAttr(default_factory=Classes)
    classes: Classes.provide(description="Classes of the element, if any")

    def __init__(self, **data):
        super().__init__(**data)
        if self.element_id is None:
            self.element_id = f"schorle-{self.tag.value.lower()}-{id(self)}" if self.element_id is None else self.element_id

    def _add_classes(self, element: LxmlElement):
        container = []
        for source in [self.classes, self._base_classes]:
            _rendered = source.render()
            if _rendered:
                container.append(_rendered)
        if container:
            element.set("class", " ".join(container))
