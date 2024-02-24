from __future__ import annotations

from abc import ABC, abstractmethod


class Renderable(ABC):

    @abstractmethod
    def render(self):
        pass

    def __call__(self):
        self.render()
