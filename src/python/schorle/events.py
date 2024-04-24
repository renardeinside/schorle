import asyncio
from functools import partial

from loguru import logger
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket

from schorle.headers import SESSION_ID_HEADER
from schorle.session import Session


class EventsEndpoint(WebSocketEndpoint):
    encoding = "json"

    async def on_connect(self, websocket: WebSocket):
        session_id = websocket.cookies.get(SESSION_ID_HEADER)
        if session_id is None:
            await websocket.close()
            return

        session = websocket.app.state.session_manager.get_session(session_id)
        if session is None:
            await websocket.close()
            return

        if session.connected:
            await websocket.close()
            return

        await websocket.accept()
        session.connected = True
        session.io = websocket

    async def on_receive(self, websocket: WebSocket, data: dict):
        session_id = websocket.cookies.get(SESSION_ID_HEADER)
        if session_id is None:
            return

        session: Session = websocket.app.state.session_manager.get_session(session_id)
        if session is None:
            return

        # logger.info(f"Received {data} from session {session_id}")
        handler = session.handlers.get(data["handlerId"])
        if handler is None:
            return

        if "value" in data:
            _handler = partial(handler, data["value"])
        else:
            _handler = handler

        session.tasks.append(asyncio.ensure_future(_handler()))

    async def on_disconnect(self, websocket: WebSocket, close_code: int):
        session_id = websocket.cookies.get(SESSION_ID_HEADER)
        if session_id is None:
            return

        logger.info(f"Session {session_id} closed with code {close_code}")
        websocket.app.state.session_manager.remove_session(session_id)
