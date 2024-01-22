# Schorle

Server-driven UI kit for Python.

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

class Container(Div):
    p1: Paragraph = Paragraph(text=Text("Hello"))
    p2: Paragraph = Paragraph(text=Text("World"))


class MyPage(Page):
    button: Button = Button.inline(text=Text("Click me!"))
    container: Container = Container.inline()

```

There can also be dynamic elements:

```python

class MyPage(Page):
    button: Button = Button.inline(text=Text("Click me!"))
    dynamic: DynamicElement = DynamicElement.inline()

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

class MyPage(Page):
    button: Button = Button.inline(text=Text("Click me!"))
    paragraphs: Collection[Div] = Collection.inline()

    def __init__(self, **data):
        super().__init__(**data)
        self.button.add_callback("click", self.on_click)

    async def on_click(self):
        if random.random() > 0.5:
            new_pargraphs = [Div(text=Text("Clicked!"))]
        else:
            new_pargraphs = []
        await self.paragraphs.update(new_pargraphs)

```

Dynamic collections and elements can also be nested.

### Reactivity

To call something in response to a client-side event, use either `@reactive` or `add_callback`.

1. React to a client-side event with `@reactive`:

```python

class MyButton(Button):
    @reactive("click")
    async def on_click(self):
        await self.text.update("Clicked!")
```

2. React to a client-side event with `add_callback`:

```python

class MyPage(Page):
    button: Button = Button.inline(text=Text("Click me!"))
    p: Paragraph = Paragraph(text=Text("Not clicked!"))

    def __init__(self, **data):
        super().__init__(**data)
        self.button.add_callback("click", self.on_click)

    async def on_click(self):
        await self.p.text.update("Clicked!")
```

### State

