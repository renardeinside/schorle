from functools import partial
from typing import Annotated, Awaitable, Callable, Iterator, Type

from loguru import logger
from lxml.etree import Element as LxmlElementFactory
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from schorle.elements.tags import HTMLTag

# str is a key for the event, Any is the value
Subscriber = Callable[["Element"], Awaitable[None]]


class Element(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    classes: str | None = None
    tag: HTMLTag
    text: str | None = Field(default=None, description="Text content of the element, if any")
    style: dict[str, str] | None = Field(default=None, description="Style attributes of the element, if any")
    element_id: str | None = Field(default=None, description="Explicitly set the id of the element, if required")
    _lxml_element: LxmlElement = PrivateAttr()
    _subscriber: Subscriber | None = PrivateAttr(default=None)
    _last_rendered: str | None = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._lxml_element = LxmlElementFactory(self.tag.value)

    def __apply_attrs(self, attrs: dict[str, str]):
        for k, v in attrs.items():
            if v is not None:
                self._lxml_element.set(k, v)

    def _find_and_apply_attrs(self):
        _attrs = {
            v.alias if v.alias else k: getattr(self, k)
            for k, v in self.model_fields.items()
            if v.json_schema_extra and v.json_schema_extra.get("attribute")
        }
        self.__apply_attrs(_attrs)
        if self.classes is not None:
            self._lxml_element.set("class", self.classes)

    @classmethod
    def provide(cls, *args, **kwargs) -> Type["Element"]:
        return Annotated[cls, Field(default_factory=partial(cls, *args, **kwargs))]

    def _traverse_elements(self, nested: bool) -> Iterator["Element"]:
        for k, v in self.model_fields.items():
            if isinstance(v.annotation, type) and issubclass(v.annotation, Element):
                element = getattr(self, k)
                yield element
                if nested:
                    yield from element._traverse_elements(nested)

        for k, v in self.model_computed_fields.items():
            if issubclass(v.return_type, Element):
                element = getattr(self, k)
                yield element
                if nested:
                    yield from element._traverse_elements(nested)

    def render(self) -> str:
        self._lxml_element.clear()
        if self.element_id is not None:
            self._lxml_element.set("id", self.element_id)
        if self.style is not None:
            self._lxml_element.set("style", ";".join([f"{k}:{v}" for k, v in self.style.items()]))
        self._find_and_apply_attrs()
        if self.text is not None:
            self._lxml_element.text = self.text
        else:
            for child in self._traverse_elements(nested=False):
                child.render()
                self._lxml_element.append(child._lxml_element)
        self._last_rendered = tostring(self._lxml_element).decode("utf-8")
        return self._last_rendered

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.tag.value}>"

    async def update(self):
        await self._subscriber(self)

    def set_subscriber(self, subscriber: Subscriber):
        logger.debug(f"Setting subscriber for {self.element_id}")
        self._subscriber = subscriber


class ElementWithGeneratedId(Element):
    def __init__(self, **data):
        super().__init__(**data)
        self.element_id = f"schorle-{self.tag.value.lower()}-{id(self)}" if self.element_id is None else self.element_id
