from typing import Any

from loguru import logger

from schorle.effector import EffectorProtocol
from schorle.render_controller import RenderControllerMixin
from schorle.utils import render_in_context


class Suspense(RenderControllerMixin):
    def __init__(self, on: EffectorProtocol, view: Any):
        self.on = on
        self._parent = None
        self._page_ref = self.controller.page

        async def _pre_action():
            logger.debug(f"Pre-action for {self.on} is called with page {self._page_ref} and view {view}")
            _view = render_in_context(view())
            self._parent.append(_view)
            self._page_ref.append_to_queue(self._parent)

        self.on.prepend(_pre_action)