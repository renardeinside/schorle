from schorle.app import Schorle
from schorle.component import component
from schorle.element import span
from schorle.icon import icon
from schorle.text import text

app = Schorle()


@component(classes="text-2xl w-96 flex justify-center items-center p-4", tag="h1")
def example():
    icon(name="party-popper")
    with span():
        text("Welcome to Schorle!")


@app.get("/")
def home():
    return example()
