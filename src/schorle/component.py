from abc import abstractmethod

from schorle.elements.base import BaseElement


class Component:
    @abstractmethod
    async def render(self) -> BaseElement:
        """Component rendering logic goes here."""

    def __str__(self):
        return f"<Component {self.__class__.__name__}>"
