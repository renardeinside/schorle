from lxml import etree

from schorle.classes import Classes
from schorle.component import Component
from schorle.context_vars import CURRENT_PARENT
from schorle.element import button
from schorle.text import text


class Button(Component):
    def render(self):
        with button(classes=Classes("btn btn-primary")):
            text("Hey!")


def test_context_rendering():
    btn = Button()
    CURRENT_PARENT.set(etree.Element("fragment"))
    btn.render()
    print(etree.tostring(CURRENT_PARENT.get()).decode())
