from pydantic import BaseModel


class ClientMessage(BaseModel):
    trigger: str
    target: str
    value: str | None = None
