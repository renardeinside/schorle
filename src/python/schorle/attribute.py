from pydantic import BaseModel


class Attribute(BaseModel):
    alias: str
    value: str

    def __init__(self, alias: str, value: str):
        super().__init__(**{"alias": alias, "value": value})


class Id(Attribute):
    alias: str = "id"
    value: str

    def __init__(self, value: str):
        super().__init__(**{"alias": "id", "value": value})
