from typing import Callable

from pydantic.dataclasses import dataclass


@dataclass
class On:
    trigger: str
    callback: Callable
    ws_based: bool = True
