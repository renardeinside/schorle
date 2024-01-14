from __future__ import annotations

from enum import Enum
from inspect import ismethod

from loguru import logger
from pydantic import BaseModel

from schorle.elements.attribute import Attribute
from schorle.state import is_injectable


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
            v.serialization_alias if v.serialization_alias else k: getattr(self, k)
            for k, v in self.model_fields.items()
            if v.json_schema_extra and v.json_schema_extra.get("attribute")
        }


class SendMixin(BaseModel):
    ws_send: str = Attribute(default="", alias="ws-send")


class InjectableMixin:
    """
    Handles the injection of state into the element.
    """

    def get_injectables(self) -> list:
        injectables = []
        for attr in dir(self):
            if attr not in ["__fields__", "__fields_set__", "__signature__"] and ismethod(getattr(self, attr)):
                if is_injectable(getattr(self, attr)):
                    logger.debug(f"{self}.{attr} is injectable")
                    injectables.append(getattr(self, attr))
        return injectables
