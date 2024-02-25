from __future__ import annotations

from enum import Enum

import msgpack
from pydantic import BaseModel


class ClientMessage(BaseModel):
    trigger: str
    target: str
    value: str | None = None

    @classmethod
    def decode(cls, message: bytes) -> ClientMessage:
        unpacked = msgpack.unpackb(message, raw=False)
        return cls(**unpacked)


class Action(str, Enum):
    morph = "morph"
    clear = "clear"


class ServerMessage(BaseModel):
    target: str
    payload: str | None = None
    action: Action

    def encode(self) -> bytes:
        return msgpack.packb(self.model_dump())
