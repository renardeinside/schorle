from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.elements.button import Button
from schorle.elements.html import Div, Paragraph
from schorle.elements.inputs import Input
from schorle.elements.page import Page
from schorle.observables.classes import Classes
from schorle.observables.text import Text
from schorle.state import Depends, State, Uses
from schorle.utils import on

app = Schorle()


class TodoList(BaseModel):
    items: list[str] = Field(default_factory=lambda: ["Buy milk", "Buy eggs", "Buy bread"])

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, item):
        self.items.remove(item)


@app.state
class AppState(State):
    todo_list: TodoList = TodoList()


class InputSection(Div):
    classes: Classes = Classes("flex flex-row justify-center items-center w-6/12 space-x-4")
    input_text: Input = Input(placeholder="Enter text here")
    add_button: Button = Button(text="Add", classes=Classes("btn-primary"))

    def pre_render(self):
        self.add_button.callback = self._on_click

    async def _on_click(self, todo_list: TodoList = Uses[AppState.todo_list]):
        if self.input_text.value:
            todo_list.add_item(self.input_text.value)
            await self.input_text.clear()


class RemoveButton(Button):
    text: str = "Remove"
    classes: Classes = Classes("btn-error")
    item: str = Field(...)

    async def on_click(self, todo_list: TodoList = Uses[AppState.todo_list]):
        todo_list.remove_item(self.item)


class TodoItem(Div):
    classes: Classes = Classes("w-full flex flex-row justify-between items-center")
    remove_button: RemoveButton


class TodoView(Div):
    classes: Classes = Classes("flex w-96 flex-col space-y-4 p-4")
    headline: Paragraph = Paragraph(text=Text("Todo List"), classes=Classes("text-2xl text-center"))
    todo_items: list[TodoItem] = Field(default_factory=list)

    @on(status="load")
    async def on_update(self, todo_list: TodoList = Depends[AppState.todo_list]):
        if not todo_list.items:
            await self.headline.text.update("Todo List is empty")
            self.todo_items.clear()
        else:
            await self.headline.text.update(f"Todo List has {len(todo_list.items)} items")
            self.todo_items = [TodoItem(text=item, remove_button=RemoveButton(item=item)) for item in todo_list.items]
        await self.update()


class TodoPage(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    input_section: InputSection = InputSection()
    todo_view: TodoView = TodoView()


@app.get("/")
def get_page():
    return TodoPage()
