import json
from functools import partial

import altair as alt
import pandas as pd
from pydantic import Field
from vega_datasets import data

from schorle.app import Schorle
from schorle.attrs import Classes, On
from schorle.card import Card
from schorle.chart import Chart
from schorle.component import Component
from schorle.element import div, link, p
from schorle.page import Page
from schorle.state import ReactiveModel, effector
from schorle.text import text

app = Schorle(
    extra_assets=[partial(link(href="https://fonts.googleapis.com/css2?family=Roboto&display=swap", rel="stylesheet"))]
)


def add_default_props(chart: alt.Chart) -> alt.Chart:
    return chart.properties(
        width="container",
        height="container",
    ).configure(font="Roboto")


class State(ReactiveModel):
    cars_data: pd.DataFrame | None = None
    selected: pd.DataFrame | None = None

    async def get_scatter(self):
        if self.cars_data is None:
            self.cars_data = data.cars()

        brush = alt.selection_interval()

        points = add_default_props(
            alt.Chart(self.cars_data)
            .mark_point()
            .encode(
                x="Horsepower:Q", y="Miles_per_Gallon:Q", color=alt.condition(brush, "Origin:N", alt.value("lightgray"))
            )
            .add_params(brush)
        )

        return points

    @effector
    async def set_selection(self, raw_info: str):
        selection = json.loads(raw_info)
        if selection:
            hp_min, hp_max = selection["Horsepower"]
            mpg_min, mpg_max = selection["Miles_per_Gallon"]
            hp_condition = self.cars_data["Horsepower"].between(hp_min, hp_max)
            mpg_condition = self.cars_data["Miles_per_Gallon"].between(mpg_min, mpg_max)
            self.selected = self.cars_data[hp_condition & mpg_condition]
        else:
            self.selected = None

    async def get_grouped_bar(self):
        if self.selected is not None:
            chart = alt.Chart(self.selected).mark_bar().encode(x="Origin:N", y="count()", color="Origin:N")
            return add_default_props(chart)


class TableView(Component):
    state: State

    def _body_view(self):
        if self.state.selected is not None:
            Chart(chart=self.state.get_grouped_bar, classes=Classes("h-full w-full"))

    def render(self):
        _title = (
            "Stats by origin in selection" if self.state.selected is not None else "Please select a region on the chart"
        )
        Card(title=_title, body=self._body_view, classes=Classes("h-full"))

    def initialize(self):
        self.bind(self.state)


class PageWithChart(Page):
    classes: Classes = Classes("p-4")
    state: State = State.factory()
    style: dict[str, str] = Field(default={"font-family": "Roboto"})

    def _scatter(self):
        Chart(
            chart=self.state.get_scatter, classes=Classes("h-full w-full"), on=On("selection", self.state.set_selection)
        )

    def render(self):
        with p(classes=Classes("text-2xl font-bold m-4")):
            text("Cars data visualization example")

        with div(classes=Classes("flex flex-row space-x-4 h-screen")):
            Card(title="Sample scatter plot", body=self._scatter, classes=Classes("h-4/6 w-4/6"))
            TableView(state=self.state, classes=Classes("w-2/6 h-4/6"))


@app.get("/")
def get_page():
    return PageWithChart()
