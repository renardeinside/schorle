from abc import ABC, abstractmethod

from pydantic import BaseModel

from schorle.context_vars import CURRENT_PARENT


class Component(ABC, BaseModel):
    def add(self):
        if CURRENT_PARENT.get() is None:
            raise ValueError("Components can only be rendered inside a parent element")
        else:
            self.render()

    @abstractmethod
    def render(self):
        pass

    def __call__(self):
        self.add()

    def __repr__(self):
        return f"<{self.__class__.__name__}/>"

    def __str__(self):
        return self.__repr__()
