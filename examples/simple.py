from schorle.app import Page, Schorle
from schorle.html import div, input_
from schorle.proto_gen.schorle import InputChangeEvent

app = Schorle()


def print_func(val: InputChangeEvent):
    print("Received input change event", val)


@app.route("/")
async def root():
    return Page(
        div(
            "Sample app", cls="card-title pb-10",
        ),
        input_(
            input_type="range",
            min="0", max="100", cls="range range-md range-primary", step="1", on_change=print_func,
            id='schorle-range'
        ),
        cls="card bg-base-200 w-100 m-10 p-10",
    )
