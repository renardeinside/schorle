from pathlib import Path

from lxml import etree

from schorle.attribute import Attribute, Id
from schorle.classes import Classes
from schorle.context_vars import CURRENT_PARENT, PAGE_CONTEXT
from schorle.on import On


class Element:
    def __init__(self, tag_name, **attributes):
        self.tag_name = tag_name
        self.attributes = attributes
        self.element = self._get_element()

    def _get_element(self):
        parent = CURRENT_PARENT.get()
        _element = None
        if parent is None:
            _element = etree.Element(self.tag_name)
        else:
            _element = etree.SubElement(parent, self.tag_name)

        provided_id = next(
            (value for key, value in self.attributes.items() if isinstance(value, Id)),
            None,
        )

        if provided_id is not None:
            _element.attrib["id"] = provided_id.value
        elif not provided_id and PAGE_CONTEXT.get():
            _element.attrib["id"] = f"sle-{self.tag_name}-{id(_element)}"

        for key, value in self.attributes.items():
            if isinstance(value, Attribute):
                _element.attrib[value.alias] = value.value
            elif isinstance(value, Classes):
                current = Classes(_element.attrib.get("class", ""))
                current.append(value)
                _element.attrib["class"] = current.render()
            elif isinstance(value, dict) and key == "style":
                if len(value) > 0:
                    _element.attrib[key] = "; ".join([f"{k}: {v}" for k, v in value.items()])
            elif isinstance(value, Path) and key == "src":
                _element.attrib[key] = f"data:image/svg+xml;utf8,{value.read_text()}"
            elif isinstance(value, On):
                _element.attrib["hx-trigger"] = value.trigger
                if value.ws_based:
                    _element.attrib["ws-send"] = ""
            else:
                _element.attrib[key] = str(value) if value is not None else ""

        if self.tag_name in ["script", "link"]:
            _element.text = ""  # prevent lxml from adding a self-closing tag

        if PAGE_CONTEXT.get():
            _element.attrib["hx-swap-oob"] = "morph"

        return _element

    def __enter__(self):
        CURRENT_PARENT.set(self.element)
        return self.element

    def __exit__(self, exc_type, exc_val, exc_tb):
        if CURRENT_PARENT.get() is not None and CURRENT_PARENT.get().getparent() is not None:
            CURRENT_PARENT.set(CURRENT_PARENT.get().getparent())

    def add(self):
        with self:
            pass


def div(**attributes):
    return Element("div", **attributes)


def span(**attributes):
    return Element("span", **attributes)


def button(**attributes):
    return Element("button", **attributes)


def link(**attributes):
    return Element("link", **attributes)


def html(**attributes):
    return Element("html", **attributes)


def head(**attributes):
    return Element("head", **attributes)


def body(**attributes):
    return Element("body", **attributes)


def title(**attributes):
    return Element("title", **attributes)


def meta(**attributes):
    return Element("meta", **attributes)


def script(**attributes):
    return Element("script", **attributes)


def footer(**attributes):
    return Element("footer", **attributes)


def p(**attributes):
    return Element("p", **attributes)


def img(**attributes):
    return Element("img", **attributes)


def a(**attributes):
    return Element("a", **attributes)
