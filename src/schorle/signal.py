class Signal:
    def __init__(self, init_value) -> None:
        self.value = init_value
        self._effects = []

    def update(self, value):
        self.value = value

    def __repr__(self):
        return f"Signal[{self.value}]"

    def add_effect(self, effect_func):
        self._effects.append(effect_func)


def effect(signal: Signal):
    def decorator(func):
        signal.add_effect(func)
        func.effect_for = signal
        return func

    return decorator


def depends(*signals: Signal):
    def decorator(func):
        func.depends_on = list(signals)
        return func

    return decorator
