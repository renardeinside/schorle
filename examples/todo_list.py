from schorle.elements.classes import Classes
from schorle.elements.html import Div
from schorle.elements.inputs import Input
from schorle.elements.page import Page
from schorle.elements.button import Button
from schorle.app import Schorle

app = Schorle()


class TodoList:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, item):
        self.items.remove(item)


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

    async def on_click(self, todo_list: TodoList = Effects(AppState.todo_list)):
        todo_list.remove_item(self.index)


class TodoItem(Div):
    remove_button: RemoveButton


class TodoListSection(Div):
    todo_items: ElementList[TodoItem] = Field(default_factory=ElementList)

    async def on_update(self, todo_list: TodoList = Depends(AppState.todo_list)):
        async with self.todo_items.suspend():
            for i, item in enumerate(todo_list.items):
                await self.todo_items.append(TodoItem(text=item, remove_button=RemoveButton(index=i)))


class PageWithButton(Page):
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen bg-gray-100")
    input_section: InputSection = InputSection()
    todo_list_section: TodoListSection = TodoListSection()


@app.get("/")
def get_page():
    return PageWithButton()
