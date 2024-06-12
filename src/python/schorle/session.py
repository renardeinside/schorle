from dataclasses import dataclass, field
from typing import Any, Callable
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
    state: dict[str, Any] = field(default_factory=dict)

    def register_handler(self, handler: Callable):
        if handler in self.handlers.inverse:
            return self.handlers.inverse[handler]

        new_uuid = f"event-{uuid4()}"
        self.handlers[new_uuid] = handler
        return new_uuid

    async def morph(self, target: str, html: str, config: dict[str, str] | None = None):
        config = {"ignoreActiveValue": False, "morphStyle": "outerHTML"} if config is None else config
        if self.io is not None:
            _message = {"event": "morph", "target": target, "html": html, "config": config}
            # logger.info(f"Sending morph message: {_message}")
            await self.io.send_json(_message)
            # logger.info(f"Morph message sent")
        else:
            raise ValueError("Session is not connected")

    async def plotly(self, target: str, _payload: str):
        if self.io is not None:
            _message = {"event": "plotly", "target": target, "payload": _payload}
            await self.io.send_json(_message)
        else:
            raise ValueError("Session is not connected")
