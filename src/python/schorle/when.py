from schorle.signal import Signal


class _When:
    def __init__(self, reactive: Signal[bool] | bool):
        self.reactive = reactive if isinstance(reactive, Signal) else Signal(reactive)
        self._classes_in_condition: str | None = None

    def then(self, classes: str):
        self._classes_in_condition = classes
        return self

    def otherwise(self, classes: str):
        return self._classes_in_condition if self.reactive.val else classes

    def __str__(self):
        return self._classes_in_condition if self.reactive.val else ""


def when(reactive: Signal[bool] | bool) -> _When:
    return _When(reactive)
