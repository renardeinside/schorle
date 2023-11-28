from schorle.app import Schorle
from schorle.elements.fmt import fmt
from schorle.elements.html import button, div, p
from schorle.page import Page
from schorle.signal import Signal

app = Schorle(theme="synthwave")

counter_signal = Signal(0)


@app.route("/")
async def index():
    @counter_signal.effect
    def increment(value):
        counter_signal.update(value + 1)

    @counter_signal.effect
    def clear(_):
        counter_signal.update(0)

    with Page() as page:
        with div() as d:
            d.add(fmt("Sample Schorle App"))
        with div():
            button("Increment", on_click=increment)
            button("Clear", on_click=clear)
        p(fmt("Clicked {} times", counter_signal), depends_on=[counter_signal])

    return page
