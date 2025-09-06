from schorle.app import Schorle
from fastapi import FastAPI

app = FastAPI()

ui = Schorle(
    project_root=".",  # or Path(__file__).parent
    cwd=".schorle",  # where your server.ts lives
    socket_path="/tmp/bun-nextjs.sock",
)

ui.mount(app)


@app.get("/")
async def index():
    return await ui.render("Index")
