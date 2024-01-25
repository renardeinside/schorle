from typing import Optional

from loguru import logger
from pydantic import Field

from schorle.elements.base.base import BaseElement
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag
from schorle.utils import reactive


class Page(Element):
    tag: HTMLTag = HTMLTag.DIV
    element_id: str = "schorle-page"

    def find_by_id(self, element_id: str) -> Optional[BaseElement]:
        for child in self.traverse():
            if child.element_id == element_id:
                return child
        return None

    def inject_page_reference(self):
        for element in self.traverse(skip_self=True):
            if isinstance(element, Element):
                for attr_name, field in element.model_fields.items():
                    if field.json_schema_extra and field.json_schema_extra.get("page_reference"):
                        setattr(element, attr_name, self)

    def __init__(self, **data):
        super().__init__(**data)

    @reactive("load")
    async def load(self):
        logger.info("Page load")
        self.inject_page_reference()


def PageReference():  # noqa: N802
    return Field(None, json_schema_extra={"attribute": False, "page_reference": True})
