class Signal:
    def __init__(self, init_value) -> None:
        self.value = init_value

    def effect(self, func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        return self, wrapper

    def set(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)
