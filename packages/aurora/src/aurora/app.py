from fastapi import FastAPI, Request
from schorle.app import Schorle
from aurora import models
from aurora.api import api
from datetime import datetime

app = FastAPI()

app.include_router(api)

ui = Schorle()
ui.mount(app)

ui.add_to_model_registry(models)


@app.get("/")
def index(req: Request):
    return ui.render(
        ui.pages.Index,
        props=models.StatsProps(
            total_users=100, last_updated_at=datetime.now().isoformat()
        ),
        req=req,
    )


@app.get("/about")
def about(req: Request):
    return ui.render(
        ui.pages.About,
        req=req,
    )


@app.get("/stats")
def stats(req: Request):
    return ui.render(
        ui.pages.Stats,
        props=models.StatsProps(
            total_users=100, last_updated_at=datetime.now().isoformat()
        ),
        req=req,
    )
