from schorle.renderable import Renderable
from schorle.state import ReactiveModel
from schorle.types import LXMLElement


class Suspense(Renderable):
    def __init__(self, on: ReactiveModel, fallback: Renderable):
        self.on = on
        self._parent: LXMLElement | None = None
        # self._page_ref = self.controller.page
        #
        # async def _pre_action():
        #     if self._parent is None:
        #         logger.warning("Parent is not set")
        #         return
        #     else:
        #         _copy = deepcopy(self._parent)
        #         required_attrs = ["id", "class", "style", "hx-swap-oob"]
        #         _saved = {k: _copy.get(k) for k in required_attrs}
        #         _copy.clear()
        #         for k, v in _saved.items():
        #             if v is not None:
        #                 _copy.set(k, v)
        #         _copy.append(self._fallback)
        #         self._page_ref.append_to_queue(_copy)
        #
        # for effector_info in on.get_effectors():
        #     effector_info.method.prepend(_pre_action)
        pass

    def set_parent(self, parent: LXMLElement):
        self._parent = parent
