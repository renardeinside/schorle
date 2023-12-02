from schorle.elements.base import BaseElement


class Page(BaseElement):
    def __init__(self, cls=None, **attrs):
        attrs["id"] = "schorle-page"
        attrs["class"] = cls
        super().__init__("div", **attrs)

    def find_by_id(self, target_id) -> BaseElement | None:
        for element in self.traverse():
            if callable(element) and "effect_for" in element.__dict__:
                continue

    #
    # def find_signals(self):
    #     """find all signals in the page"""
    #     signals = []
    #     for element in self._traverse(self):
    #         print(element)
    #     return signals
