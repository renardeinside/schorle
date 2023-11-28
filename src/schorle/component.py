from schorle.signal import Signal


def component(depends_on: list[Signal]):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # inject signal values into args
            return func(*args, **kwargs)

        wrapper.depends_on = depends_on
        return wrapper

    return decorator
