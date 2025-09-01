from fastapi import FastAPI
from aurora.ui.app import app as ui_app

app = FastAPI()

app.mount("/dist", ui_app.static_files())


@app.get("/")
async def read_root():
    return ui_app.to_response("Index")
