from pydantic import Field

from schorle.elements.base.element import Element
from schorle.elements.html import Div
from schorle.elements.img import Img
from schorle.elements.tags import HTMLTag
from schorle.reactives.classes import Classes


class Figure(Element):
    tag: HTMLTag = HTMLTag.FIGURE


class FigureWithImg(Figure):
    img: Img


class CardTitle(Element):
    tag: HTMLTag = HTMLTag.H2
    _base_classes: Classes = Classes("card-title")


class CardActions(Div):
    _base_classes: Classes = Classes("card-actions")


class CardBody(Div):
    _base_classes: Classes = Classes("card-body")
    title: CardTitle = Field(default_factory=CardTitle)
    body: Div = Field(default_factory=Div)
    actions: CardActions | None = None


class Card(Div):
    _base_classes: Classes = Classes("card")
    figure: Element | Figure | None = None
    body: CardBody = Field(default_factory=CardBody)
