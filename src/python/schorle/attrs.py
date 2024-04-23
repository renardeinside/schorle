from dataclasses import dataclass
from typing import Callable

from schorle.reactive import Reactive


@dataclass
class On:
    event: str
    handler: Callable


@dataclass
class Bind:
    property: str
    reactive: Reactive
