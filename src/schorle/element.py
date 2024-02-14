from lxml import etree

from schorle.classes import Classes
from schorle.context_vars import RENDER_CONTROLLER
from schorle.tags import HTMLTag


class Element:
    def __init__(self, tag: HTMLTag, element_id: str | None = None, **attributes):
        self.tag = tag.value
        self.attributes = attributes
        self.element_id = element_id
        self._element = self.get_element()
        self.apply_attributes()

    @property
    def controller(self):
        return RENDER_CONTROLLER.get()

    def get_element(self):
        elem = etree.SubElement(self.controller.current, self.tag)
        if self.tag in [HTMLTag.SCRIPT, HTMLTag.LINK]:
            elem.text = ""  # Prevents self-closing tags
        return elem

    def apply_attributes(self):
        # TODO: Refactor this method
        for key, value in self.attributes.items():
            if isinstance(value, dict) and len(value) == 0:
                continue
            elif isinstance(value, dict) and key == "style":
                value = " ".join([f"{k}: {v};" for k, v in value.items()])
            elif isinstance(value, Classes):
                value = value.render()
                if not value:
                    continue
                else:
                    self._element.set("class", value)
            elif not value:
                continue

            self._element.set(key, str(value))

    def __enter__(self):
        self.controller.previous = self.controller.current
        self.controller.current = self._element

        if self.element_id:
            self._element.set("id", self.element_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.controller.current = self.controller.previous
        pass

    def add(self):
        with self:
            pass

    def __repr__(self):
        return f"<{self.tag} {'id=%s' % self.element_id if self.element_id else ''}/>"

    def __str__(self):
        return self.__repr__()


def div(**attributes):
    return Element(HTMLTag.DIV, **attributes)


def span(**attributes):
    return Element(HTMLTag.SPAN, **attributes)


def button(**attributes):
    return Element(HTMLTag.BUTTON, **attributes)


def link(**attributes):
    return Element(HTMLTag.LINK, **attributes)


def html(**attributes):
    return Element(HTMLTag.HTML, **attributes)


def head(**attributes):
    return Element(HTMLTag.HEAD, **attributes)


def body(**attributes):
    return Element(HTMLTag.BODY, **attributes)


def title(**attributes):
    return Element(HTMLTag.TITLE, **attributes)


def meta(**attributes):
    return Element(HTMLTag.META, **attributes)


def script(**attributes):
    return Element(HTMLTag.SCRIPT, **attributes)


def footer(**attributes):
    return Element(HTMLTag.FOOTER, **attributes)


def p(**attributes):
    return Element(HTMLTag.P, **attributes)


def img(**attributes):
    return Element(HTMLTag.IMG, **attributes)


def a(**attributes):
    return Element(HTMLTag.A, **attributes)
