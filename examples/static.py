from schorle.app import Schorle
from schorle.component import Component
from schorle.element import h1, span
from schorle.icon import icon
from schorle.text import text

app = Schorle()


class ExamplePage(Component):
    def render(self):
        with h1(classes="text-2xl w-96 flex justify-center items-center p-4"):
            icon(name="party-popper")
            with span():
                text("Welcome to Schorle!")


@app.get("/")
def home():
    return ExamplePage()
