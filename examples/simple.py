from loguru import logger

from schorle.app import Schorle
from schorle.elements.fmt import fmt
from schorle.elements.html import button, div, p
from schorle.page import Page

app = Schorle()

counter_signal = app.signal(0)


@app.route("/")
async def index():
    @counter_signal.effect
    def increment(value):
        logger.info(f"Incrementing {value}")
        counter_signal.update(value + 1)
        logger.info(f"New value: {counter_signal.value}")

    @counter_signal.effect
    def clear(value):
        logger.info(f"Clearing {value}")
        counter_signal.update(0)
        logger.info(f"New value: {counter_signal.value}")

    with Page(theme="light", **{"class": "h-screen flex justify-center p-10"}) as page:
        with div(**{"class": "card h-64 w-96 bg-base-100 shadow-2xl flex justify-center"}):
            p("Schorle app", **{"class": "text-center"})
            with div(**{"class": "flex flex-row justify-evenly p-10"}):
                button("Click me", on_click=increment, **{"class": "btn btn-primary"})
                button("Clear", on_click=clear, **{"class": "btn btn-secondary"})
            p(fmt("Clicked {} times", counter_signal), depends_on=[counter_signal], **{"class": "text-center"})

    return page
