from schorle.elements.classes import Classes
from schorle.elements.html import Div
from schorle.elements.inputs import Input
from schorle.elements.page import Page
from schorle.elements.button import Button
from schorle.app import Schorle

app = Schorle()


class StateContainer:
    input = Input(placeholder="Enter text here")


class AppState(State):
    input = provide(Input, placeholder="Enter text here")
    todo_list = provide(TodoList)


class InputSection(Div):
    input_text: Input = Input(placeholder="Enter text here")
    add_button: Button = Button(text="Add")

    def initialize(self):
        self.add_button.callback = self._on_click

    async def _on_click(self):
        self.todo_list.add_item(self.input_text.value)
        await self.input_text.clear()


class RemoveButton(Button):
    index: int

    async def on_click(self, todo_list: TodoList = Provide[AppState.todo_list]):
        todo_list.remove_item(self.index)


class TodoItem(Div):
    remove_button: RemoveButton


class TodoListSection(Div):
    todo_items: list[TodoItem] = Field(default_factory=list)

    async def on_update(self, todo_list: TodoList = Depends[AppState.todo_list]):
        for i, item in enumerate(todo_list.items):
            self.todo_items.append(TodoItem(text=item, remove_button=RemoveButton(index=i)))
        await self.todo_items.update()


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen bg-gray-100")
    input_section: InputSection = InputSection()
    todo_list_section: TodoListSection = TodoListSection()


@app.get("/")
def get_page():
    return PageWithButton()
