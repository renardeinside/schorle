from copy import deepcopy
from typing import Any

from loguru import logger

from schorle.render_controller import RenderControllerMixin
from schorle.state import ReactiveModel
from schorle.types import LXMLElement
from schorle.utils import render_in_context


class Suspense(RenderControllerMixin):
    def __init__(self, on: ReactiveModel, fallback: Any):
        self.on = on
        self._parent: LXMLElement | None = None
        self._page_ref = self.controller.page
        self._fallback = render_in_context(fallback, None)

        async def _pre_action():
            if self._parent is None:
                logger.warning("Parent is not set")
                return
            else:
                _copy = deepcopy(self._parent)
                required_attrs = ["id", "class", "style", "hx-swap-oob"]
                _saved = {k: _copy.get(k) for k in required_attrs}
                _copy.clear()
                for k, v in _saved.items():
                    if v is not None:
                        _copy.set(k, v)
                _copy.append(self._fallback)
                self._page_ref.append_to_queue(_copy)

        for effector_info in on.get_effectors():
            effector_info.method.prepend(_pre_action)
