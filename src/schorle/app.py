from typing import Dict

from schorle.elements.page import Page
from schorle.theme import Theme


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK) -> None:
        self.routes: Dict[str, Page] = {}
        self.theme: Theme = theme

    def get(self, path: str):
        def decorator(func):
            self.routes[path] = func()
            return func

        return decorator
