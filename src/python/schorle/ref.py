from typing import Generic, TypeVar

T = TypeVar("T")


class Ref(Generic[T]):
    current: T

    def set(self, value: T):
        self.current = value
