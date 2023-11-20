from vdom import button, div

from schorle.app import Page, Schorle

app = Schorle()


@app.route("/")
async def root():
    _p = Page(
        div("Hello"),
        button("blah", attributes={"class": "btn btn-primary"})
    )
    return _p