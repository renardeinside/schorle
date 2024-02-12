from typing import Callable

import pydantic


@pydantic.dataclasses.dataclass
class On:
    trigger: str
    callback: Callable
