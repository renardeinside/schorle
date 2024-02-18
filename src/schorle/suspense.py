from copy import deepcopy
from typing import Any

from loguru import logger

from schorle.effector import EffectorProtocol
from schorle.render_controller import RenderControllerMixin
from schorle.types import LXMLElement
from schorle.utils import render_in_context


class Suspense(RenderControllerMixin):
    def __init__(self, on: EffectorProtocol, fallback: Any):
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
                _copy.text = ""
                _copy.append(self._fallback)
                for key in ["hx-trigger", "ws-send"]:
                    if key in _copy.attrib:
                        _copy.attrib.pop(key)
                self._page_ref.append_to_queue(_copy)

        self.on.prepend(_pre_action)
