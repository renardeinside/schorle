from fastapi import FastAPI
from aurora.ui import Index, bootstrap

app = FastAPI()
bootstrap(app)


@app.get("/")
def index():
    return Index()
