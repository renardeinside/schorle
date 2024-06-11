from typing import Literal, TypeVar, ParamSpec, Callable

StoreType = Literal["session", "component"]

P = ParamSpec("P")
T = TypeVar("T")


def store(scope: StoreType = "session") -> T:
    def decorator(func: Callable[P, T]) -> T:
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


class Depends:
    def __init__(self, func):
        self.func = func
