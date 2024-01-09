from __future__ import annotations

from enum import Enum
from functools import partial
from inspect import isclass
from types import GenericAlias, UnionType
from typing import Annotated, Callable, Iterator, get_origin

from loguru import logger
from lxml.etree import Element as LxmlElementFactory
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from pydantic.fields import FieldInfo

from schorle.elements.attribute import Attribute
from schorle.elements.tags import HTMLTag
from schorle.observable import ObservableModel, Subscriber
from schorle.utils import wrap_in_coroutine


class ObservableElement(ObservableModel):
    _selected_fields: list[str] = PrivateAttr(default=["text", "style", "classes", "element_id", "_trigger"])
    _trigger: str | None = PrivateAttr(default=None)

    def update(self):
        """
        Explicitly update the element.
        :return:
        """
        self._trigger = str(id(self))


class Bootstrap(str, Enum):
    ON_LOAD = "on_load"
    BEFORE_RENDER = "before_render"


class AttrsMixin(BaseModel):
    """
    Handles the attributes of the element.
    Attributes should be defined as fields with the `Attribute` annotation.
    """

    @property
    def attrs(self):
        return {
            v.alias if v.alias else k: getattr(self, k)
            for k, v in self.model_fields.items()
            if v.json_schema_extra and v.json_schema_extra.get("attribute")
        }


class BindableMixin(BaseModel):
    _on_loads: list[Callable] = PrivateAttr(default_factory=list)
    _pre_renders: list[Callable] = PrivateAttr(default_factory=list)
    _binds: list[Callable] = PrivateAttr(default_factory=list)

    def bind(
        self,
        observable: ObservableModel,
        effect: Callable,
        *,
        bootstrap: Bootstrap | None = None,
    ):
        # wrap the effect in a coroutine if it isn't one
        _effect = wrap_in_coroutine(effect)

        subscriber = Subscriber()
        observable.subscribe(subscriber)

        async def _effect_subscriber():
            async for _ in subscriber:
                logger.info(f"Calling effect {effect} with {observable}")
                await _effect(observable)
                logger.info(f"Called effect {effect} with {observable}")

        self._binds.append(_effect_subscriber)

        if bootstrap == Bootstrap.ON_LOAD:
            self._on_loads.append(partial(_effect, observable))
        elif bootstrap == Bootstrap.BEFORE_RENDER:
            self._pre_renders.append(partial(_effect, observable))

    def get_binds(self):
        return self._binds

    def get_on_loads(self):
        return self._on_loads

    def get_pre_renders(self):
        return self._pre_renders


class Element(ObservableElement, AttrsMixin, BindableMixin):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    classes: str | None = None
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

    def get_element(self) -> LxmlElement:
        if self._rendering_element is None:
            element = LxmlElementFactory(self.tag.value)

            if self.element_id is not None:
                element.set("id", self.element_id)

            if self.style is not None:
                element.set("style", ";".join([f"{k}:{v}" for k, v in self.style.items()]))

            if self.classes is not None:
                element.set("class", self.classes)

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

    def __init__(self, **data):
        super().__init__(**data)
        self.element_id = f"schorle-{self.tag.value.lower()}-{id(self)}" if self.element_id is None else self.element_id
