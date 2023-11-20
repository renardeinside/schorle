import asyncio
import sys
from typing import Annotated

from loguru import logger
from schorle.app import BackendApp
from schorle.dev import AppLoader, DevServer
from schorle.proto_gen.schorle import ReloadEvent
from typer import Argument, Typer
from uvicorn import Config
from watchfiles import awatch

cli_app = Typer(name="schorle")


@cli_app.command(name="dev")
def dev(
    app: Annotated[str, Argument(..., help='App import string in format "<module>:<attribute>')],
    host: str = "0.0.0.0",
    port: int = 4444,
):
    # we need two processes here - one for the app and one to watch the changes and send a reload message
    # app is served as an uvicorn Server
    # changes are watched by watchfiles

    # so we can load the app from the import string
    sys.path.insert(0, ".")
    loader = AppLoader(app)

    backend_app = BackendApp()
    dev_config = Config(backend_app.app, host=host, port=port, reload=False, lifespan="off")
    dev_server = DevServer(dev_config)

    async def _serve():
        logger.info("Starting server")
        await dev_server.serve()

    async def _watch():
        new_instance = loader.reload_and_get_instance()
        await backend_app.reflect_routes(new_instance)

        while not backend_app.ws:
            logger.info("Waiting for websocket connection")
            await asyncio.sleep(1)

        logger.info("Websocket connection established")

        async for _ in awatch(".", recursive=True):
            logger.info("Changes detected, reloading...")
            new_instance = loader.reload_and_get_instance()
            await backend_app.reflect_routes(new_instance)
            await backend_app.ws.send_bytes(bytes(ReloadEvent()))

    async def main():
        server_task = asyncio.create_task(_serve())
        watch_task = asyncio.create_task(_watch())
        await asyncio.gather(server_task, watch_task)

    asyncio.run(main())


def entrypoint():
    cli_app()
