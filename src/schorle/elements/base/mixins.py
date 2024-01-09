from __future__ import annotations

from enum import Enum
from functools import partial
from typing import Callable

from loguru import logger
from pydantic import BaseModel, PrivateAttr, ConfigDict

from schorle.elements.classes import Classes
from schorle.observable import ObservableModel, Subscriber
from schorle.utils import wrap_in_coroutine
from lxml.etree import _Element as LxmlElement


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
