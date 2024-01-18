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

Elements are the building blocks of your UI. You can easily combine them to create complex UIs.

There are two types of elements:
- Persistent elements - you cannot remove them from the page (but you can hide them).
- Dynamic elements - you can change their structure on the fly.

- Both persistent and dynamic elements support changing their attributes, `Classes` and `Text`.

#### Persistent elements


here is a quick example for a div with paragraph and button inside:

```python

class DivWithButton(Div):
   p: Paragraph = Paragraph.field(text=Text("some text"))
   b: Button = Button.field(text=Text("click me"))
```

As you can see, you can perform pretty much everything, e.g. change the `text` of the `Paragraph` or `Button` element.

However, you cannot remove the `Paragraph` or `Button` element from the `Div` element. 
To support this, you need to use dynamic elements.


#### Dynamic elements

There are two types of dynamic elements:

- Single dynamic elements - you can only have one instance of this element inside the parent element.
- Elements list - you can have multiple instances of this element inside the parent element.

Here is a quick example:

```python

class PersistentWithDynamicChild(Div):
  optional_button: Dynamic[Button] = Dynamic.field()

  async def on_update(self, ...): # called when the element is updated, see below
    if self.optional_button.is_empty():
      await self.optional_button.update(Button(text=Text("click me")))
    else:
      await self.optional_button.remove()
```

And here is a quick example for an elements list:

```python

class PersistentWithList(Div):
  buttons: DynamicList[Button] = DynamicList.field()

  async def on_update(self, ...): # can be called in various situations, see below
      new_buttons = [Button(text=Text(f"button {i}")) for i in range(10)]
      await self.buttons.update(new_buttons)

```

Please note that `Dynamic` elements can only be updated via `await element.update(...)` operations.


#### `Text` and `Classes` fields of elements

Any `Element` comes with two predefined fields:
- `Text` - a text field.
- `Classes` - a list of classes.

Both of these fields are dynamic, and support the same update operations as any other dynamic element:

```python

class DivWithText(Div):
  text: Text = Text("some text")

  async def on_update(self, ...):
    await self.text.update("some text")
    await self.classes.toggle("some-class")
```

### Pages

`Page` is a special element that represents the whole page. It is the root element of the UI tree.
Pages are defined as follows:

```python

class MyPage(Page):
  state: PageState = PageState()
  div: Div = Div.field()
  button: Button = Button.field()
```


### Routes


Routes are used to map URLs to pages. They are defined as follows:

```python
from schorle.app import Schorle

app = Schorle()


class MyPage(Page):
    # state: PageState = PageState() explained below
    div: Div = Div.field()
    button: Button = Button.field()

@app.get("/")
def index():
    return MyPage()
```

### State


State is a special class that is used to store the state of the page. 

It is defined and used as follows:

```python
from schorle.state import State, Uses, Depends


class PageState(State):
    counter: int = 0

class MyButton(Button):
  text: Text = Text("click me")

  @reactive("click") # defines a mapping between the click event and the on_click method
  async def on_click(self, counter: int = Uses[PageState.counter]): # Note the format - Uses[className.fieldName]
    counter.value += 1
 
  async def on_update(self, counter: int = Depends[PageState.counter]):  # Note the format - Depends[className.fieldName]
    await self.text.update(f"clicked {counter} times")

class MyPage(Page):
    state: PageState = PageState()
```

State is initialized every time when user opens a page. 

To send updates to the state, always use the `Uses` annotation in the relevant method.
To read the state, always use the `Depends` annotation in the relevant method. 
All methods with `Depends[State.field]` annotation will be fired when the state changes.


### Reactivity


`Reactivity` is a mechanism that allows you to map events to methods. To make a method reactive, use the `@reactive` decorator:

```python

@reactive("click")
async def on_click(self):
  ...


@reactive("mouseover")
async def on_mouseover(self):
  ...
```