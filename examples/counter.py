import asyncio

from schorle.app import Schorle
from schorle.components import Card
from schorle.elements.html import button, p
from schorle.page import Page
from schorle.renderer import Renderer
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


@app.route("/")
async def index():
    with Page() as page:
        with page.layout:
            with Card() as card:
                with card.container.layout:
                    with card.body.layout:
                        with card.title.layout:
                            p("Hello world").add()
                        p("hey there").add()
                        with card.actions.layout:
                            button("Click me too", cls="btn btn-primary").add()

    return page
