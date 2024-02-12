import contextvars
from typing import Callable

from lxml.etree import _Element as LxmlElement

CURRENT_PARENT: contextvars.ContextVar[LxmlElement | None] = contextvars.ContextVar("CURRENT_PARENT", default=None)
PAGE_CONTEXT: contextvars.ContextVar[bool] = contextvars.ContextVar("page_context", default=False)
REACTIVES: contextvars.ContextVar[dict[str, Callable]] = contextvars.ContextVar("action_map", default={})
