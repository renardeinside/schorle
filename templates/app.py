from fastapi import FastAPI
from aurora.ui import pages, ui
from datetime import datetime

app = FastAPI()

ui.mount(app)


@app.get("/")
async def index():
    return await ui.render(pages.Index)


@app.get("/stats")
async def stats():
    return await ui.render(
        pages.Stats,
        props={"total_users": 100, "last_updated_at": datetime.now().isoformat()},
    )
