from typing import Callable

import plotly.express as px
from loguru import logger
from plotly.graph_objs import Figure

from schorle.app import Schorle
from schorle.attrs import On
from schorle.component import Component, component
from schorle.element import span
from schorle.session import Session

app = Schorle(title="Schorle | Plotly chart")


def get_figure() -> Figure:
    df = px.data.iris()
    fig = px.scatter(
        df, x="sepal_width", y="sepal_length", color="species", size="petal_length", hover_data=["petal_width"]
    )
    return fig


class Plotly(Component):
    fig_provider: Callable[[], Figure]

    def initialize_with_session(self, session: Session):

        async def on_connect():
            logger.info("Loading plotly figure")

        self.on = On("connect", on_connect)

    def render(self):
        span(classes="loading loading-bars loading-md text-primary")


@component()
def main():
    Plotly(fig_provider=get_figure)


@app.get("/")
def index():
    return main()
