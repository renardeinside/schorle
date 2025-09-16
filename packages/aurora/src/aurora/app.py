from fastapi import FastAPI, Request
from schorle.app import Schorle

app = FastAPI()

ui = Schorle()
ui.mount(app)


@app.get("/")
def index(req: Request):
    return ui.render(ui.pages.Index, props=dict(title="Hello, World!"), req=req)
