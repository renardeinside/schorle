from loguru import logger

from schorle import Page, Schorle, button, code, div, p
from schorle.elements.fmt import fmt

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
            p("Sample app using ", code("Schorle"), **{"class": "text-center card-title"}),
            div(
                button("Click me", on_click=increment, **{"class": "btn btn-primary"}),
                button("Clear", on_click=clear, **{"class": "btn btn-secondary"}),
                **{"class": "flex flex-row justify-evenly"},
            ),
            p(fmt("Clicked {} times", counter_signal), depends_on=[counter_signal], **{"class": "text-center"}),
            **{"class": "card w-100 h-96 m-10 bg-base-100 shadow-xl rounded-box p-10 flex flex-column justify-between"},
        ),
        **{"class": "flex flex-col items-center justify-center h-screen"},
    )
