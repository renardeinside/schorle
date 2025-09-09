from fastapi import FastAPI
from aurora.ui import pages, ui
from datetime import datetime
from aurora import models

app = FastAPI()

ui.mount(app)
ui.add_to_model_registry(models)


@app.get("/")
async def index():
    return await ui.render(pages.Index)


@app.get("/stats")
async def stats():
    return await ui.render(
        pages.Stats,
        props=models.StatsProps(
            total_users=100, last_updated_at=datetime.now().isoformat()
        ),
    )
