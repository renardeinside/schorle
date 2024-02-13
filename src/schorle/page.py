from abc import abstractmethod

from pydantic import Field

from schorle.attribute import Id
from schorle.classes import Classes
from schorle.component import Component
from schorle.context_vars import PAGE_CONTEXT
from schorle.element import div


class Page(Component):
    classes: Classes = Classes()
    style: dict[str, str] = Field(default_factory=dict)

    @abstractmethod
    def render(self):
        pass

    def __enter__(self):
        PAGE_CONTEXT.set(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        PAGE_CONTEXT.set(False)

    def __call__(self):
        with div(_id=Id("schorle-page"), classes=self.classes, style=self.style):
            self.render()
