from loguru import logger

from schorle import Schorle, Page, div, button, p
from schorle.html import fmt

app = Schorle()

counter_signal = app.signal(0)


@app.route("/")
async def index():
    @counter_signal.effect
    def increment(value):
        logger.info(f"Incrementing {value}")
        counter_signal.set(value + 1)
        logger.info(f"New value: {counter_signal.value}")

    @counter_signal.effect
    def clear(value):
        logger.info(f"Clearing {value}")
        counter_signal.set(0)
        logger.info(f"New value: {counter_signal.value}")

    return Page(
        div(
            "Sample app using Schorle",
            div(
                button("Click me", on_click=increment, **{"class": "btn btn-primary"}),
                button("Clear", on_click=clear, **{"class": "btn btn-secondary"}),
            ),
            p(
                fmt("Clicked {} times", counter_signal),
                depends_on=[counter_signal],
            ),
            **{"class": "card w-100 bg-base-100 shadow-xl rounded-box p-10 flex h-50"}
        ),
        **{"class": "flex flex-col items-center justify-center h-screen"}
    )
