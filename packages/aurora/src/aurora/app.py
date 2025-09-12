from pathlib import Path
from fastapi import FastAPI
from schorle.app import Schorle

app = FastAPI()

ui = Schorle()
ui.mount(app)


@app.get("/")
def index():
    return ui.render(Path("Index.tsx"))
