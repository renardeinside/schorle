from typing import Callable, Literal, ParamSpec, TypeVar

from schorle.session import Session
from schorle.signal import Signal

ScopeType = Literal["session", "component"]

P = ParamSpec("P")
T = TypeVar("T")


def store_wrapper(scope: ScopeType = "session") -> T:
    def decorator(func: Callable[P, T]) -> T:
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.scope = scope
        return wrapper

    return decorator


class Depends:
    def __init__(self, func):
        self.func = func
        self.scope: ScopeType = func.scope

    def get_instance(self, session: Session | None = None):
        if self.scope == "component":
            return self.func()
        else:
            if not session:
                raise ValueError("Session is required for session-scoped dependencies")

            index = str(id(self.func))
            if index not in session.state:
                session.state[index] = self.func()
            return session.state[index]


def store(initial_value: T, scope: ScopeType = "session"):
    def _provider():
        return Signal(initial_value)

    return store_wrapper(scope)(_provider)
