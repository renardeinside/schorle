from functools import partial

from lxml.etree import Element as LxmlElementFactory
from lxml.etree import _Element as LxmlElement
from lxml.etree import tostring
from pydantic import BaseModel, ConfigDict, PrivateAttr

from schorle.elements.tags import HTMLTag


class Element(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    classes: str | None = None
    tag: HTMLTag
    text: str | None = None
    element_id: str | None = None
    _lxml_element: LxmlElement = PrivateAttr()

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

    def _find_renderable_fields(self):
        for k, v in self.model_fields.items():
            if isinstance(v.annotation, type) and issubclass(v.annotation, Element):
                yield k

        for k, v in self.model_computed_fields.items():
            if issubclass(v.return_type, Element):
                yield k

    def render(self) -> str:
        self._lxml_element.clear()
        if self.element_id is not None:
            self._lxml_element.set("id", self.element_id)
        self._find_and_apply_attrs()
        if self.text is not None:
            self._lxml_element.text = self.text
        else:
            children = self._find_renderable_fields()
            for field in children:
                field_value = getattr(self, field)
                if isinstance(field_value, Element):
                    field_value.render()
                    self._lxml_element.append(field_value._lxml_element)

        return tostring(self._lxml_element, pretty_print=True).decode("utf-8")

    @classmethod
    def factory(cls, *args, **kwargs):
        return partial(cls, *args, **kwargs)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.tag.value}>"


class ElementWithGeneratedId(Element):
    def __init__(self, **data):
        super().__init__(**data)
        self.element_id = f"schorle-{self.tag.value.lower()}-{id(self)}"
