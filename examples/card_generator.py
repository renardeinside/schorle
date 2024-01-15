from random import randint

from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.elements.button import Button
from schorle.elements.card import Card, CardBody, CardTitle, FigureWithImg
from schorle.elements.html import Div
from schorle.elements.img import Img
from schorle.elements.page import Page
from schorle.observables.classes import Classes
from schorle.state import Depends, State, Uses
from schorle.utils import on

app = Schorle()


class CardInfo(BaseModel):
    title: str
    text: str
    img_src: str


@app.state
class AppState(State):
    cards: list[CardInfo] = Field(
        default_factory=lambda: [
            CardInfo(
                title=f"Card {index}",
                text=f"This is card {index}",
                img_src=f"https://picsum.photos/id/{randint(1, 200)}/600",  # noqa: S311
            )
            for index in range(3)
        ]
    )


class AddCardButton(Button):
    text: str = "Add Card"
    classes: Classes = Classes("btn-primary")

    async def on_click(self, cards: list[CardInfo] = Uses[AppState.cards]):
        cards.append(
            CardInfo(
                title=f"Card {len(cards) + 1}",
                text=f"This is card {len(cards) + 1}",
                img_src=f"https://picsum.photos/id/{randint(0, 200)}/600",  # noqa: S311
            )
        )


class CardsView(Div):
    classes: Classes = Classes("grid md:grid-cols-3 gap-4 pt-3")
    cards_list: list[Card] = Field(default_factory=list)

    @on("load")
    async def on_update(self, cards: list[CardInfo] = Depends[AppState.cards]):
        self.cards_list.clear()
        for card in cards:
            self.cards_list.append(
                Card(
                    classes=Classes("shadow-2xl"),
                    figure=FigureWithImg(img=Img(src=card.img_src, alt=card.title)),
                    body=CardBody(title=CardTitle(text=card.title), body=Div(text=card.text)),
                )
            )
        await self.update()


class CardsPage(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center p-4")
    add_card_button: AddCardButton = AddCardButton()
    cards_view: CardsView = CardsView()


@app.get("/")
def get_page():
    return CardsPage()
