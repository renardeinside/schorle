from functools import partial

from pydantic import Field

from schorle.elements.inputs import Input
from schorle.app import Schorle
from schorle.elements.base.mixins import Bootstrap
from schorle.elements.button import Button
from schorle.elements.html import Div, Paragraph
from schorle.elements.page import Page
from schorle.observable import ObservableModel
from schorle.theme import Theme

app = Schorle(theme=Theme.DARK)


class State(ObservableModel):
    items: list[str] = Field(default_factory=lambda: ["Buy milk", "Buy eggs"])

    def add_item(self, item: str):
        self.items = [*self.items, item]

    def remove_item(self, item_index: int):
        self.items = [*self.items[:item_index], *self.items[item_index + 1:]]


class InputLine(Div):
    classes: str = "flex flex-row space-x-4 w-8/12 justify-center items-center"
    input_: Input.provide(placeholder="Start typing here...")
    add_button: Button.provide(text="Add", classes="btn btn-primary")


class TodoItem(Div):
    classes: str = "card shadow-xl p-4 w-8/12 justify-between items-center flex flex-row space-x-4 animate-[pulse_1s]"
    info: Div.provide()
    remove_button: Button.provide(text="Remove", classes="btn btn-error")


class TodoList(Div):
    classes: str = "flex flex-col space-y-2 w-10/12 justify-center items-center"
    items: list[TodoItem] = Field(default_factory=list)

    async def delete_item(self, state, item_index: int):
        state.remove_item(item_index)
        self.update()

    def on_update(self, state: State):
        self.items = [
            TodoItem(
                info=Div(text=item),
                remove_button=Button(
                    text="Done!", classes="btn btn-success", on_click=partial(self.delete_item, state, index)
                ),
            )
            for index, item in enumerate(state.items)
        ]
        self.update()


class TodoPage(Page):
    state: State = State()
    classes: str = "space-y-10 h-screen p-2 flex flex-col items-center justify-center"
    advice: Paragraph.provide(text="Please type below to add items to your list", classes="text-2xl")
    input_line: InputLine.provide()
    todos: TodoList.provide()


@app.get("/")
def index():
    page = TodoPage()

    def on_add_button_click():
        page.state.add_item(page.input_line.input_.value)
        page.input_line.input_.clear()

    page.input_line.add_button.set_callback(on_add_button_click)
    page.todos.bind(page.state, page.todos.on_update, bootstrap=Bootstrap.ON_LOAD)
    return page
