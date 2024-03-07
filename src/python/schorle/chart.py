import json
from typing import Callable

from schorle.attrs import On
from schorle.component import Component
from schorle.loading import Loading
from schorle.models import Action, ServerMessage


class Chart(Component):
    chart: Callable
    with_actions: bool = False
    loaded: bool = False

    def render(self):
        if not self.loaded:
            Loading(instant_render=True)

    def initialize(self):
        if isinstance(self.on, On):
            self.on = [self.on]

        _on = self.on or []
        _on.append(On(trigger="load", callback=self.load))
        self.on = _on

    async def load(self, _):
        _chart = await self.chart()
        if not _chart:
            return
        _json = _chart.to_json()
        _msg = ServerMessage(
            action=Action.render, target=self.element_id, payload=_json, meta=json.dumps({"actions": self.with_actions})
        )
        await self.page_ref.io.send_bytes(_msg.encode())
        self.loaded = True

    async def update(self):
        await self.load(None)
