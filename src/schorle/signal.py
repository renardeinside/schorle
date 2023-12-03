from contextvars import ContextVar

SIGNALS: ContextVar[dict[str, "Signal"]] = ContextVar("signals", default={})


class Signal:
    def __init__(self, init_value) -> None:
        self.value = init_value
        self.effects = {}
        self.dependants = []
        self._id = str(id(self))
        SIGNALS.get()[self._id] = self

    def update(self, value):
        self.value = value

    def __repr__(self):
        return f"Signal[{self.value}]"

    def add_effect(self, effect_func):
        self.effects[effect_func.__name__] = effect_func
        effect_func.signal_id = self._id


def effect(signal: Signal):
    def decorator(func):
        signal.add_effect(func)
        func.effect_for = signal
        return func

    return decorator


def depends(*signals: Signal):
    def decorator(func):
        for signal in signals:
            signal.dependants.append(func)
        return func

    return decorator
