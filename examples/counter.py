import asyncio
from random import randint

from schorle.app import Schorle
from schorle.component import Component
from schorle.elements.html import button, div, p, span
from schorle.page import Page
from schorle.reactive import reactive

app = Schorle(theme="dark")


@app.route("/")
async def index():
    class ReactiveButton(Component):
        def __init__(self):
            self.counter = reactive(0)
            self.button = button(self.message, on_click=self.on_click, cls="btn btn-primary")
            self.counter_view = p(self.message, cls="card-title")
            self.conditional_view = p("This is only visible when counter is odd", cls="invisible")
            self.loading = span(cls="loading loading-ring loading-lg")

        @property
        def message(self):
            return f"Clicked {self.counter.value} times"

        async def on_click(self):
            await self.button.update(self.loading)
            await asyncio.sleep(randint(1, 3))

            self.counter.update(self.counter.value + 1)
            await self.button.update(self.message)
            await self.counter_view.update(self.message)

            if self.counter.value % 2 == 0:
                await self.conditional_view.update(cls="invisible")
            else:
                await self.conditional_view.update(cls="visible text-bg-primary")

        async def render(self):
            with div(cls="card w-96 bg-neutral text-neutral-content m-4") as card:
                with div(cls="card-body") as d:
                    d.add(self.counter_view)
                    d.add(self.conditional_view)
                    d.add(self.button)

                card.add(d)

            return card

    b1 = ReactiveButton()
    b2 = ReactiveButton()

    with Page() as page:
        with div(cls="h-screen flex justify-center items-center") as d:
            d.add(b1)
            d.add(b2)
            page.add(d)

    return page
