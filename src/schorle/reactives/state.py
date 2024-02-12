from pydantic import BaseModel

from schorle.effector import effector_listing, inject_effectors


class ReactiveModel(BaseModel, extra="allow"):
    def __init__(self, **data):
        super().__init__(**data)
        inject_effectors(self)

    def get_effectors(self):
        yield from effector_listing(self)


class ReactiveState:
    def __init__(self):
        inject_effectors(self)
