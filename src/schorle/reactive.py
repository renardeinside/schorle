from contextvars import ContextVar

REACTIVES: ContextVar[dict[str, "Reactive"]] = ContextVar("reactives", default={})


class Reactive:
    def __init__(self, initial_value):
        self.reactive_id = str(id(self))
        self._value = initial_value
        REACTIVES.get()[self.reactive_id] = self
        self.subscribers = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def update(self, new_value):
        self._value = new_value

    @property
    def value(self):
        return self._value


def reactive(initial_value):
    return Reactive(initial_value)
