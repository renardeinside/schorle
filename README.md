<p align="center">
    <img src="https://raw.githubusercontent.com/renardeinside/schorle/main/raw/with_text.svg" class="align-center" height="150" alt="logo" />
</p>

**`Schorle` (pronounced as [ˈʃɔʁlə](https://en.wikipedia.org/wiki/Schorle)) is a server-driven UI kit for Python with
async support.**

---

<p align="center">
    <img src="https://img.shields.io/pypi/v/schorle?color=green&amp;style=for-the-badge" alt="Latest Python Release"/>
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge" alt="We use black for formatting"/>
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

### Elements

Elements are the building blocks of a UI. The entrypoint to build a UI is the `Page` class.

```python
from schorle.elements.page import Page


class MyPage(Page):
    pass

```

Elements can be nested.

```python
from schorle.elements.button import Button
from schorle.elements.html import Div, Paragraph
from schorle.elements.page import Page
from schorle.reactives.text import Text


class Container(Div):
    p1: Paragraph = Paragraph(text=Text("Hello"))
    p2: Paragraph = Paragraph(text=Text("World"))


class MyPage(Page):
    button: Button = Button.factory(text=Text("Click me!"))
    container: Container = Container.factory()
```

There can also be dynamic elements:

```python
from schorle.elements.base.element import Reactive
from schorle.elements.button import Button
from schorle.elements.html import Div, Paragraph
from schorle.elements.page import Page
from schorle.reactives.text import Text
import random


class MyPage(Page):
    button: Button = Button.factory(text=Text("Click me!"))
    reactive_element: Reactive = Reactive.factory()

    def __init__(self, **data):
        super().__init__(**data)
        self.button.add_callback("click", self.on_click)

    async def on_click(self):
        if random.random() > 0.5:
            self.dynamic.update(Paragraph(text=Text("Clicked!")))
        else:
            await self.dynamic.update(Div(text=Text("Not clicked!")))

```

As well as dynamic collections:

```python
from schorle.elements.button import Button
from schorle.elements.html import Div
from schorle.elements.page import Page
from schorle.reactives.text import Text
from schorle.elements.base.element import Collection
import random


class MyPage(Page):
    button: Button = Button.factory(text=Text("Click me!"))
    paragraphs: Collection[Div] = Collection.factory()

    def __init__(self, **data):
        super().__init__(**data)
        self.button.add_callback("click", self.on_click)

    async def on_click(self):
        if random.random() > 0.5:
            new_paragraphs = [Div(text=Text("Clicked!"))]
        else:
            new_paragraphs = []
        await self.paragraphs.update(new_paragraphs)

```

Dynamic collections and elements can also be nested.

### Reacting to client-side events

To call something in response to a client-side event, use either `@reactive` or `add_callback`.

- React to a client-side event with `@reactive`:

```python
from schorle.elements.button import Button
from schorle.utils import reactive


class MyButton(Button):
    @reactive("click")
    async def on_click(self):
        await self.text.update("Clicked!")
```

- React to a client-side event with `add_callback`:

```python
from schorle.elements.button import Button
from schorle.elements.html import Paragraph
from schorle.elements.page import Page
from schorle.reactives.text import Text


class MyPage(Page):
    button: Button = Button.factory(text=Text("Click me!"))
    p: Paragraph = Paragraph(text=Text("Not clicked!"))

    def __init__(self, **data):
        super().__init__(**data)
        self.button.add_callback("click", self.on_click)

    async def on_click(self):
        await self.p.text.update("Clicked!")
```

### Server-side effects

To call some updates from the server-side, use `@effector` decorator in combination with `subscribe` method:

```python

from __future__ import annotations

from schorle.app import Schorle
from schorle.effector import effector
from schorle.elements.button import Button
from schorle.elements.page import Page
from schorle.reactives.classes import Classes
from schorle.reactives.state import ReactiveModel
from schorle.reactives.text import Text
from schorle.utils import reactive

app = Schorle()


class Counter(ReactiveModel):
    value: int = 0

    @effector  # effector transforms a method into an effect generating function
    async def increment(self):
        self.value += 1


class ButtonWithCounter(Button):
    text: Text = Text("Click me!")
    counter: Counter = Counter.factory()

    @reactive("click")
    async def handle(self):
        await self.counter.increment()

    async def _on_increment(self, counter: Counter):
        await self.text.update(f"Clicked {counter.value} times")
        await self.classes.toggle("btn-success")

    async def before_render(self):
        await self.counter.increment.subscribe(self._on_increment)  # subscribe to the effect


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    first_button: ButtonWithCounter = ButtonWithCounter.factory()
    second_button: ButtonWithCounter = ButtonWithCounter.factory()


@app.get("/")
def get_page():
    return PageWithButton()

```

## Running the application

Schorle application is a thin wrapper around [FastAPI](https://fastapi.tiangolo.com/). To run the application,
use `uvicorn`:

```bash
uvicorn examples.simple:app --reload
```

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) - web framework
- [HTMX](https://htmx.org/) - client-side library for dynamic HTML
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [DaisyUI](https://daisyui.com/) - Component library for Tailwind CSS
- [Pydantic](https://docs.pydantic.dev/latest/) - classes and utilities for elements


## Roadmap

- [ ] Add more elements
- [ ] Introduce `suspense` for loading states
- [ ] Add more examples
- [ ] Add tests
- [ ] Add CI/CD
- [ ] Add documentation
- [ ] Add support for Plotly-based charts
- [ ] Refactor the imports