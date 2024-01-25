from pydantic import BaseModel

from schorle.effector import inject_effectors


class ReactiveModel(BaseModel, extra="allow"):
    def __init__(self, **data):
        super().__init__(**data)
        inject_effectors(self)


class ReactiveState:
    def __init__(self):
        inject_effectors(self)
