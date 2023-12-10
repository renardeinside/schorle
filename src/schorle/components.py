from schorle.elements.html import div


class Card:
    def __init__(self):
        self.container = div(cls="card card w-96 bg-base-100 shadow-xl")
        self.body = div(cls="card-body")
        self.title = div(cls="card-title")
        self.actions = div(cls="card-actions")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
