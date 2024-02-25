from typing import Any

from schorle.render_queue import RENDER_QUEUE
from schorle.renderable import Renderable
from schorle.state import ReactiveModel


class Suspense:
    def __init__(self, on: ReactiveModel, fallback: Renderable):
        self.on = on
        self.fallback = fallback
        self.parent: Any | None = None

        async def _pre_action():
            RENDER_QUEUE.get().put_nowait(self.generate)

        for effector_info in on.get_effectors():
            effector_info.method.prepend(_pre_action)
        pass

    def generate(self):
        with self.parent():
            self.fallback()
