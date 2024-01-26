from pydantic import BaseModel

from schorle.effector import inject_effectors
from schorle.elements.base.mixins import FactoryMixin


class ReactiveModel(BaseModel, FactoryMixin, extra="allow"):
    def __init__(self, **data):
        super().__init__(**data)
        inject_effectors(self)


class ReactiveState:
    def __init__(self):
        inject_effectors(self)
