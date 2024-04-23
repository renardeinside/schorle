from dataclasses import dataclass
from typing import Callable


@dataclass
class On:
    event: str
    handler: Callable
