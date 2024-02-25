from schorle.render_queue import RENDER_QUEUE
from schorle.state import ReactiveModel


class Bindable:
    def bind(self, reactive_model: ReactiveModel):
        def _emitter():
            RENDER_QUEUE.get().put_nowait(self)

        for effector_info in reactive_model.get_effectors():
            effector_info.method.subscribe(_emitter)
