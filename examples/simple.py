from pathlib import Path

from schorle.app import Schorle
from schorle.elements.fmt import fmt
from schorle.elements.html import button, div, p
from schorle.page import Page

app = Schorle(theme="synthwave", css_extras=[Path("./styles.css")])

counter_signal = app.signal(0)


@app.route("/")
async def index():
    @counter_signal.effect
    def increment(value):
        counter_signal.update(value + 1)

    @counter_signal.effect
    def clear(_):
        counter_signal.update(0)

    with Page() as page:
        with div(**{"class": "text-4xl"}):
            fmt("Sample Schorle App")

        with div():
            button("Increment", on_click=increment)
            button("Clear", on_click=clear)

        p(fmt("Clicked {} times", counter_signal), depends_on=[counter_signal])

    return page
