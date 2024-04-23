from dataclasses import dataclass, field
from typing import Callable
from uuid import uuid4

from bidict import bidict
from starlette.websockets import WebSocket


@dataclass
class Session:
    uuid: str
    connected: bool = False
    io: WebSocket | None = None
    handlers: bidict[str, Callable] = field(default_factory=bidict)
    tasks: list = field(default_factory=list)

    def register_handler(self, handler: Callable):
        if handler in self.handlers.inverse:
            return self.handlers.inverse[handler]

        new_uuid = f"event-{uuid4()}"
        self.handlers[new_uuid] = handler
        return new_uuid

    async def morph(self, target: str, html: str):
        if self.io is not None:
            await self.io.send_json({"event": "morph", "target": target, "html": html})
        else:
            raise ValueError("Session is not connected")
