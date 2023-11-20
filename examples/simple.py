from vdom import div, input_, p

from schorle.app import Page, Schorle

app = Schorle()


@app.route("/")
async def root():
    return Page(
        div(
            p("Example app with schorle", attributes={"class": "card-title pb-10"}),
            # p("This is a paragraph", attributes={"class": "card-title pb-10"}),
            input_(
                attributes={
                    "id": "schorle-ranger",
                    "min": "0",
                    "max": "100",
                    "value": "50",
                    "type": "range",
                    "class": "range range-md range-primary",
                    # "step": "1",
                }
            ),
            attributes={"class": "card bg-base-200 w-100 m-10 p-10"},
        ),
        cls=["h-screen", "max-w-7xl", "mx-auto", "p-4", "sm:px-6", "lg:px-8"],
    )
