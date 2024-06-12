from functools import partial
from typing import Callable

import numpy as np
import pandas as pd
import plotly.express as px
from loguru import logger
from plotly.graph_objs import Figure

from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import Component, component
from schorle.element import button, code, div, h1, pre, span
from schorle.signal import Signal
from schorle.store import Depends, Uses, store_provider
from schorle.text import text

app = Schorle(title="Schorle | Plotly chart")


def get_random_frame() -> pd.DataFrame:
    df = pd.DataFrame(np.random.randn(100, 3), columns=["x", "y", "c"])
    df["size"] = np.random.randint(1, 20, 100)
    return df


@store_provider(scope="session")
def data_store():
    return Signal(get_random_frame())


async def update_data(data: Signal[pd.DataFrame]):
    await data.update(get_random_frame())


def get_figure(data: Signal[pd.DataFrame]) -> Figure:
    return px.scatter(data(), x="x", y="y", color="c", size="size")


class Plotly(Component):
    data_signal: Signal
    plotter: Callable

    async def on_connect(self):
        logger.info(f"Connected to target: {self.element_id}")
        await self.send_update()
        logger.info(f"Sent initial data to target: {self.element_id}")

    def initialize_with_session(self):
        self.on = On("connected", self.on_connect)
        self.data_signal.subscribe(self.send_update)

    def get_figure(self):
        return self.plotter(self.data_signal)

    async def send_update(self):
        _figure: Figure = self.get_figure()
        _payload = _figure.to_json()
        await self.session.plotly(self.element_id, _payload)

    def render(self):
        with div(classes="h-96 w-96 flex align-center justify-center"):
            span(classes="loading loading-bars loading-md text-primary")


@component()
def chart(data: Signal[pd.DataFrame] = Uses(data_store)):
    return Plotly(data_signal=data, plotter=get_figure)


@component(classes="m-4 w-96")
def update_button(data: Signal[pd.DataFrame] = Uses(data_store)):
    with button(classes="btn btn-primary w-full", on=On("click", partial(update_data, data))):
        text("Update")


@component()
def table_view(data: Signal[pd.DataFrame] = Depends(data_store)):
    with div(classes="mockup-code"):
        with pre():
            with code(classes="language-json"):
                text(data().head(3).to_json(indent=4, orient="records"))


@component(classes="flex flex-col items-center justify-center m-4")
def main():
    with div(classes="grid grid-cols-4 gap-4 w-full h-full"):
        with div(classes="col-span-2"):
            with h1(classes="text-2xl font-bold text-center"):
                text("Plotly chart")
            chart()
        with div(classes="col-span-2"):
            with h1(classes="text-2xl font-bold text-center"):
                text("Sample data")
            table_view()

    update_button()


@app.get("/")
def index():
    return main()
