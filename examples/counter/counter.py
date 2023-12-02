from schorle.app import Schorle
from schorle.elements.base import dynamic
from schorle.elements.html import button, div, p
from schorle.page import Page
from schorle.signal import Signal, depends, effect

app = Schorle(theme="dark")


@app.route("/")
async def index():
    c1 = Signal(0)
    c2 = Signal(0)

    def view_group(counter: Signal):
        @effect(counter)
        async def increment():
            counter.update(counter.value + 1)

        @effect(counter)
        async def clear():
            counter.update(0)

        @depends(counter)
        async def view():
            with div(cls="text-center") as d:
                p(f"Clicked {counter.value} times")
            return d

        @depends(counter)
        @effect(counter)
        async def clear_button():
            cls = "btn btn-secondary" + (" btn-disabled" if counter.value == 0 else "")
            return button("Clear", on_click=clear, cls=cls)

        with div(cls="card bg-base-400 shadow-2xl p-4") as d:
            with div(cls="card-body items-center text-center"):
                div("Hello schorle!", cls="card-title")
                with div(cls="text-center"):
                    dynamic(view)
                with div(cls="card-actions justify-end"):
                    button("Increment", on_click=increment, cls="btn btn-primary")
                    dynamic(clear_button)
        return d

    @depends(c1, c2)
    async def summary_view():
        with div(cls="flex flex-row items-center justify-center") as d:
            with div(cls="w-96 card bg-base-400 shadow-2xl p-4"):
                with div(cls="card-body items-center text-center"):
                    div("Hello schorle!", cls="card-title")
                    with div(cls="text-center"):
                        p(f"Clicked {c1.value + c2.value} times")
        return d

    with Page(cls="h-screen") as page:
        with div(cls="flex flex-row items-center justify-center"):
            view_group(c1)
            view_group(c2)
        dynamic(summary_view)

    return page
