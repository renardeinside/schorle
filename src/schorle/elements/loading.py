from enum import Enum

from schorle.elements.html import Div, Span


class LoadingStyle(str, Enum):
    SPINNER = "loading-spinner"
    DOTS = "loading-dots"
    RING = "loading-ring"
    BALL = "loading-ball"
    BARS = "loading-bars"
    INFINITY = "loading-infinity"


class LoadingSize(str, Enum):
    SMALL = "loading-sm"
    MEDIUM = "loading-md"
    LARGE = "loading-lg"


class Loading(Div):
    classes: str = "loading"
    size: LoadingSize = LoadingSize.MEDIUM
    styling: LoadingStyle = LoadingStyle.INFINITY
    span: Span = Span.provide()

    def __init__(self, **data):
        super().__init__(**data)
        self.span.classes = f"{self.size.value} {self.styling.value}"
