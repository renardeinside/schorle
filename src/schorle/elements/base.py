import asyncio
from asyncio import Queue, iscoroutinefunction
from functools import partial
from typing import Annotated, Callable, Iterator, Type

from loguru import logger
from lxml.etree import Element as LxmlElementFactory
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from schorle.elements.tags import HTMLTag


class Subscriber:
    def __init__(self):
        self.queue: Queue = Queue()

    async def __aiter__(self):
        while True:
            await asyncio.sleep(0)  # prevent blocking
            yield await self.queue.get()


class ObservableModel(BaseModel):
    _selected_fields: list[str] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._subscribers: list[Subscriber] = []

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if not self._selected_fields or name in self._selected_fields:
            for subscriber in self._subscribers:
                logger.info(f"Sending update to {subscriber} from {self} on {name}")
                subscriber.queue.put_nowait(self)

    def subscribe(self, subscriber: Subscriber):
        logger.info(f"Subscribing {subscriber} to {self}")
        self._subscribers.append(subscriber)


class ObservableElement(ObservableModel):
    _selected_fields: list[str] = PrivateAttr(default=["text", "style", "classes", "element_id"])


class Element(ObservableElement):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    classes: str | None = None
    tag: HTMLTag
    text: str | None = Field(default=None, description="Text content of the element, if any")
    style: dict[str, str] | None = Field(default=None, description="Style attributes of the element, if any")
    element_id: str | None = Field(default=None, description="Explicitly set the id of the element, if required")
    _lxml_element: LxmlElement = PrivateAttr()
    _last_rendered: str | None = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._lxml_element = LxmlElementFactory(self.tag.value)
        self._binds: list[Callable] = []
        self._on_loads: list[Callable] = []

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

    def traverse_elements(self, *, nested: bool) -> Iterator["Element"]:
        for k, v in self.model_fields.items():
            if isinstance(v.annotation, type) and issubclass(v.annotation, Element):
                element = getattr(self, k)
                yield element
                if nested:
                    yield from element.traverse_elements(nested=nested)

        for k, v in self.model_computed_fields.items():
            if issubclass(v.return_type, Element):
                element = getattr(self, k)
                yield element
                if nested:
                    yield from element.traverse_elements(nested=nested)

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
            for child in self.traverse_elements(nested=False):
                child.render()
                self._lxml_element.append(child._lxml_element)
        self._last_rendered = tostring(self._lxml_element).decode("utf-8")
        return self._last_rendered

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.tag.value}>"

    def update_text(self, text: str):
        self.text = text

    def _wrap_in_coroutine(self, effect: Callable[[ObservableModel], None]):
        # wrap the effect in a coroutine if it isn't one

        if not iscoroutinefunction(effect):

            async def _effect(obs: ObservableModel):
                effect(obs)

        else:
            _effect = effect
        return _effect

    def bind(self, observable: ObservableModel, effect: Callable, *, on_load: bool = False):
        # wrap the effect in a coroutine if it isn't one
        _effect = self._wrap_in_coroutine(effect)

        # logger.info(f"Binding {observable} to {self} with effect {effect}")
        subscriber = Subscriber()
        observable.subscribe(subscriber)

        async def _effect_subscriber():
            logger.info(f"Subscribing {observable} to {self} with effect {effect}")
            logger.info(f"Observing {observable} with effect {effect}")
            async for _ in subscriber:
                logger.info(f"Calling effect {effect} with {observable}")
                await _effect(observable)
                logger.info(f"Called effect {effect} with {observable}")
            logger.info(f"Unsubscribing {observable} from {effect}")

        self._binds.append(_effect_subscriber)

        if on_load:
            self._on_loads.append(partial(_effect, observable))

    def get_binds(self):
        return self._binds

    def get_on_loads(self):
        return self._on_loads


class ElementWithGeneratedId(Element):
    def __init__(self, **data):
        super().__init__(**data)
        self.element_id = f"schorle-{self.tag.value.lower()}-{id(self)}" if self.element_id is None else self.element_id
