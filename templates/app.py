from fastapi import FastAPI, Request
from schorle.app import Schorle
from aurora import models
from datetime import datetime

app = FastAPI()

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
