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

### Elements

In contrast to using templating engines, Schorle uses Python functions to create HTML elements.
This approach allows for better type checking and code completion.

```python
from schorle.text import text
from schorle.element import div
from schorle.rendering_context import rendering_context


def my_element():
    with div():
        text("Hey!")


with rendering_context() as ctx:
    my_element()
    print(ctx.to_lxml())
```

Although this might seem a bit complicated, in actual applications it works nicely when Elements are used inside the
Components.

## Components

Components are reusable parts of the UI. They are created using Python classes.

```python

from schorle.component import Component
from schorle.element import div
from schorle.text import text


class MyComponent(Component):
    def render(self):
        with div():
            text("Hey!")


print(
    MyComponent().to_string()
)
```

Note that the `render` method is used to define the structure of the component.

Since `render` is a method, you can use all the power of Python to create dynamic components, like this:

```python

from schorle.component import Component
from schorle.element import div, span
from schorle.text import text


class MyComponent(Component):
    def render(self):
        with div():
            for idx in range(10):
                with span():
                    text("Hey!") if idx % 2 == 0 else text("Ho!")
```

Pretty much any Python code can be used to create the structure of the component.

## Running the application

Schorle application is a thin wrapper around [FastAPI](https://fastapi.tiangolo.com/). To run the application,
use `uvicorn`:

```bash
uvicorn examples.static:app --reload
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

On the backend:
- [FastAPI](https://fastapi.tiangolo.com/) - web framework
- [Pydantic](https://docs.pydantic.dev/latest/) - classes and utilities for elements

On the frontend:
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [DaisyUI](https://daisyui.com/) - Component library for Tailwind CSS
- [Lucide Icons](https://lucide.dev/) - Icon library


## Optimizing the site performance

`Schorle` has several features to optimize the site performance:

- Client-server communications are happening over WebSockets and inside a Worker
- CSS/JS libraries are served as brotli-compressed files

## Roadmap

- [x] Add dev reload
- [x] Add server communication channel
- [ ] Add state (global)
- [x] Add state at component level
- [ ] Add more elements
- [x] Add support for icons
- [ ] Add convenient attributes API
- [ ] Add more examples
- [ ] Add tests
- [ ] Add CI/CD
- [ ] Add documentation
- [ ] Add support for Plotly-based charts
- [ ] Add support for Vega-based charts
- [ ] Refactor the imports