from asyncio import Queue
from contextvars import ContextVar

RENDER_QUEUE: ContextVar[Queue] = ContextVar("render_queue", default=Queue())
