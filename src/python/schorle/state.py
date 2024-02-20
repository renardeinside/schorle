from pydantic import BaseModel, Field

from schorle.effector import effector_listing, inject_effectors


class EffectorMixin:
    def get_effectors(self):
        return effector_listing(self)


class ReactiveModel(BaseModel, EffectorMixin, extra="allow"):
    def __init__(self, **data):
        super().__init__(**data)
        inject_effectors(self)

    @classmethod
    def factory(cls, **data):
        return Field(default_factory=lambda: cls(**data))


class ReactiveState(EffectorMixin):
    def __init__(self):
        inject_effectors(self)
