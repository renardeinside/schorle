from schorle.app import Schorle
from schorle.elements.fmt import fmt
from schorle.elements.html import button, div, p
from schorle.page import Page
from schorle.signal import Signal

app = Schorle(theme="cyberpunk")


@app.route("/")
async def index():
    c1 = Signal(0)
    c2 = Signal(0)

    def _button_group(cs):
        @cs.effect
        def increment(value):
            cs.update(value + 1)

        @cs.effect
        def clear(_):
            cs.update(0)

        with div(**{"class": "card w-96 shadow-2xl p-4"}) as d:
            with div(**{"class": "card-body flex flex-row justify-center items-center"}):
                button("Increment", on_click=increment, **{"class": "btn btn-primary"})
                button("Clear", on_click=clear, **{"class": "btn btn-secondary"})
            with div(**{"class": "text-center"}):
                p(fmt("Clicked {} times", cs), depends_on=[cs])

        return d

    with Page() as page:
        with div(**{"class": "text-center text-4xl m-10"}):
            p("Hello schorle!")
        with div(**{"class": "flex flex-row space-x-4 justify-center items-center"}):
            _button_group(c1)
            _button_group(c2)
        with div(depends_on=[c1, c2]):
            pass

    return page
