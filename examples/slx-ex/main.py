from schorle.app import Schorle
from fastapi import FastAPI
from registry import pages

app = FastAPI()

ui = Schorle()

ui.mount(app)


@app.get("/")
async def index():
    return await ui.render(pages.Index)
