from pydantic import Field, computed_field

from schorle.app import Schorle
from schorle.elements.html import Button, Page, Span

app = Schorle()


class PageWithButton(Page):
    second_btn: Button = Field(default_factory=Button.factory(text="Go to second page", classes="btn btn-secondary"))
    home_btn: Button = Field(default_factory=Button.factory(text="Go to home page", classes="btn btn-primary"))
    counter_value: int = 0

    @computed_field
    @property
    def counter(self) -> Span:
        return Span(text=str(self.counter_value), classes="invisible")

    def on_click(self):
        self.counter_value += 1


@app.get("/")
def home() -> PageWithButton:
    return PageWithButton()
