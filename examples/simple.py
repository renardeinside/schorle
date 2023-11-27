from pathlib import Path

from loguru import logger

from schorle.app import Schorle
from schorle.elements.fmt import fmt
from schorle.elements.html import div, p, button
from schorle.page import Page

app = Schorle(theme="synthwave", css_extras=[Path("./styles.css")])

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

    with Page(class_name="page") as page:
        with div():
            button("Increment", on_click=increment)
            button("Clear", on_click=clear)
        p(fmt("Clicked {} times", counter_signal), depends_on=[counter_signal])

    return page
