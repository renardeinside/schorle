from schorle.component import Component
from schorle.element import icon
from schorle.text import text


class Icon(Component):
    name: str

    def render(self):
        with icon(**{"data-lucide": self.name}):
            text("")
