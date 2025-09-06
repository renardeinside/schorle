from schorle.app import Schorle
from fastapi import FastAPI
from registry import pages

app = FastAPI()

ui = Schorle(
    project_root=".",  # or Path(__file__).parent
)

ui.mount(app)


@app.get("/")
async def index():
    return await ui.render(pages.Index)
