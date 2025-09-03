from fastapi import FastAPI
from aurora.ui import Index, mount_assets

app = FastAPI()
mount_assets(app)


@app.get("/")
def index():
    return Index()
