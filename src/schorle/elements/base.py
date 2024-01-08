from contextlib import contextmanager
from enum import Enum
from functools import partial
from inspect import isclass
from types import UnionType
from typing import Annotated, Callable, Iterator, Optional, Type, get_origin

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
    _selected_fields: list[str] = PrivateAttr(default=["text", "style", "classes", "element_id", "_suspend"])


class Bootstrap(str, Enum):
    ON_LOAD = "on_load"
    BEFORE_RENDER = "before_render"


class AttrsMixin(BaseModel):
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

    def __init__(self, **data):
        super().__init__(**data)
        self._suspense = None
        self._suspend: bool = False

    @classmethod
    def provide(cls, *args, **kwargs) -> Type["Element"]:
        return Annotated[cls, Field(default_factory=partial(cls, *args, **kwargs))]

    def _check_annotation_args(self, anno: UnionType):
        for arg in anno.__args__:
            if isclass(arg) and get_origin(arg) not in [list, dict] and issubclass(arg, Element):
                return True
            elif isinstance(arg, UnionType):
                return self._check_annotation_args(arg)

    def _related_to_element(self, field: FieldInfo) -> bool:
        anno = field.annotation
        if isclass(anno) and issubclass(anno, Element):
            return True
        elif isinstance(anno, UnionType) and self._check_annotation_args(anno):
            return True

    def traverse_elements(self, *, nested: bool) -> Iterator["Element"]:
        for k, v in self.model_fields.items():
            if self._related_to_element(v):
                element = getattr(self, k)
                if isinstance(element, Element):
                    yield element
                    if nested:
                        yield from element.traverse_elements(nested=nested)

        for k, v in self.model_computed_fields.items():
            if issubclass(v.return_type, Element):
                element = getattr(self, k)
                yield element
                if nested:
                    yield from element.traverse_elements(nested=nested)

    @contextmanager
    def suspend(self, suspense: Optional["Element"] = None):
        # todo - passing suspense as an element through the instance state is a bit hacky
        logger.debug(f"Suspending {self}")
        self._suspend = True
        self._suspense = suspense
        yield self
        logger.debug(f"Un-suspending {self}")
        self._suspend = False

    def get_element(self, *, suspended: bool = False) -> LxmlElement:
        element = LxmlElementFactory(self.tag.value)

        if self.element_id is not None:
            element.set("id", self.element_id)

        if self.style is not None:
            element.set("style", ";".join([f"{k}:{v}" for k, v in self.style.items()]))

        if self.classes is not None:
            element.set("class", self.classes)

        if suspended:
            if self._suspense is None:
                _suspense = Element(tag=HTMLTag.SPAN, classes="loading loading-lg loading-infinity")
            else:
                _suspense = self._suspense

            element.append(_suspense.get_element())
        else:
            for k, v in self.attrs.items():
                if v is not None:
                    element.set(k, v)
            if self.text is not None:
                element.text = self.text
            else:
                for child in self.traverse_elements(nested=False):
                    element.append(child.get_element())

        return element

    def render(self) -> str:
        logger.info(f"Rendering element {self}")
        element = self.get_element(suspended=self._suspend)
        return tostring(element, pretty_print=True).decode("utf-8")

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.tag.value}>"

    def update_text(self, text: str):
        self.text = text


class ElementWithGeneratedId(Element):
    hx_swap: str = Attribute(default="morph", alias="hx-swap-oob")

    def __init__(self, **data):
        super().__init__(**data)
        self.element_id = f"schorle-{self.tag.value.lower()}-{id(self)}" if self.element_id is None else self.element_id
