<p align="center">
    <img src="https://raw.githubusercontent.com/renardeinside/schorle/main/raw/with_text.svg" class="align-center" height="150" alt="logo" />
</p>

**`Schorle` (pronounced as [ˈʃɔʁlə](https://en.wikipedia.org/wiki/Schorle)) is a server-driven UI kit for Python with
async support.**

---

<p align="center">
    <a href="https://pypi.org/project/schorle/" style="text-decoration: none">
        <img src="https://img.shields.io/pypi/v/schorle?color=green&amp;style=for-the-badge" alt="Latest Python Release"/>
    </a>
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge" alt="We use black for formatting"/>
    <a href="https://codecov.io/gh/renardeinside/schorle"  style="text-decoration: none">
        <img src="https://img.shields.io/codecov/c/gh/renardeinside/schorle?style=for-the-badge"
             alt="codecov"/>
    </a>
</p>

---

**Note:** This project is in an early stage of development. It is not ready for production use.

## Installation

```bash
pip install schorle
```

## Usage

Take a look at the [examples](examples) directory.

## Concepts

We use the following approaches to handle various cases:

- Rendering HTML elements is done using Python functions.
- `HTMX` for server interop
- `Hyperscript` for client-side scripting

### Elements

In contrast to using templating engines, Schorle uses Python functions to create HTML elements.
This approach allows for better type checking and code completion.

```python
from schorle.element import div, button


def my_element():
    return div().append(
        button().text("Click me!")
    )
```

For more complex cases, you can use with-blocks:

```python
from schorle.element import div, button


def my_element():
    with div() as container:
        container >> button().text("Click me!")
    return container
```

For multi-nesting cases, you can call tag-methods directly on the parent:

```python
from schorle.element import div, button


def my_element():
    with div() as complex_container:
        with complex_container.div() as container:
            container.button().text("Click me!")

        with complex_container.div() as another_container:
            another_container >> button().text("No, click me!")

    return complex_container

```

### Handlers

Handler is just a dataclass with information on how to handle a specific trigger, for instance:

```python
from schorle.attrs import Handler, Swap, Classes, post
from schorle.element import button, form, Element, div
from schorle.icon import icon
from schorle.app import Schorle
from fastapi import Form
from typing import Annotated

app = Schorle()


def input_component():
    with form(
            Classes("flex flex-row justify-center items-center w-96 space-x-2"),
            handler=Handler(post("/add"), "#tasks", Swap.before_end),
            hsx="""
                on htmx:afterRequest
                    my.reset()
                    add .btn-disabled to #add-button
        """,
    ) as this:
        this >> button(
            Classes("btn btn-primary btn-square btn-disabled"),
            element_id="add-button",
        ).append(icon("plus"))

    return this


def task_view(task: str) -> Element:
    return div().text(f"Task: {task}")


@app.backend.post("/add")
def add_task(task: Annotated[str, Form()]):
    return task_view(task).to_response()
```

### Client-side scripting

For client-side scripting,`Hyperscript` is used:

```python
from schorle.element import button
from schorle.attrs import Classes


def counter():
    return button(
        Classes("btn btn-primary"),
        hsx="""
            init
                set my.count to 0
            on click
                set my.count to my.count + 1
                put `Clicked ${my.count} times!` into me
            """,
    ).text("Click me!")
```

We plan to introduce a Python-to-Hyperscript transpiler in the future.
## Rendering the elements

To render a specific element as HTML Response, use the `to_response` function:

```python

from schorle.element import div
from schorle.app import Schorle

app = Schorle()


@app.backend.get("/task/{task_id:int}")
def get_task(task_id: int):
    return div().text(f"Task {task_id}").to_response()
```

To render the whole document, do it like this:

```python
from schorle.element import div
from schorle.app import Schorle

app = Schorle()


@app.backend.get("/")
def get_home():
    return app.doc.include(
        div().text("Hello, world!")
    ).to_response()

```

## Running the application

Schorle application is a thin wrapper around [FastAPI](https://fastapi.tiangolo.com/). To run the application,
use `uvicorn`:

```bash
uvicorn examples.todo:app --reload
```

Under the hood, Schorle uses FastAPI, so you can use all the features provided by FastAPI.
To access the FastAPI application instance, use the `backend` attribute:

```python
from schorle.app import Schorle

app = Schorle()

app.backend.add_middleware(...)  # add FastAPI middleware
```

## Dev reload

`Schorle` supports dev reload out of the box. To enable it, use the `--reload` flag:

```bash
uvicorn examples.todo:app --reload
```

On any change in the code, the server will restart automatically, and the client will re-fetch the page.

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) - web framework
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [DaisyUI](https://daisyui.com/) - Component library for Tailwind CSS
- [Pydantic](https://docs.pydantic.dev/latest/) - classes and utilities for elements
- [HTMX](https://htmx.org/) - server interop
- [Hyperscript](https://hyperscript.org/) - client-side scripting
-

## Roadmap

- [ ] Add more elements
- [x] Add dev reload
- [x] Add support for icons
- [x] Add support for onload events
- [ ] Python-to-Hyperscript transpiler
- [ ] Add convenient attributes API
- [ ] Add more examples
- [ ] Add tests
- [ ] Add CI/CD
- [ ] Add documentation
- [ ] Add support for Plotly-based charts
- [ ] Add support for Vega-based charts
- [ ] Refactor the imports