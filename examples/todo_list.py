from __future__ import annotations

from pydantic import BaseModel, Field

from schorle.app import Schorle
from schorle.dynamics.classes import Classes
from schorle.dynamics.element_list import Collection
from schorle.dynamics.text import Text
from schorle.elements.button import Button
from schorle.elements.html import Div, Paragraph
from schorle.elements.inputs import Input
from schorle.elements.page import Page, PageReference
from schorle.emitter import emitter, inject_emitters
from schorle.utils import before_render

app = Schorle()


class TodoList(BaseModel, extra="allow"):
    items: list[str] = Field(default_factory=lambda: ["Buy milk", "Buy eggs", "Buy bread"])

    @emitter
    async def add_item(self, item: str):
        self.items.append(item)

    @emitter
    async def remove_item(self, item: str):
        self.items.remove(item)


class InputSection(Div):
    classes: Classes = Classes("flex flex-row justify-center items-center w-6/12 space-x-4")
    input_text: Input = Input(placeholder="Enter text here")
    add_button: Button = Button(text="Add", classes=Classes("btn-primary"))
    page: TodoPage = PageReference()

    def __init__(self, **data):
        super().__init__(**data)
        self.add_button.add_callback("click", self._on_click)

    async def _on_click(self):
        new_input = self.input_text.value.get()
        if new_input:
            await self.page.todo_list.add_item(new_input)
            await self.input_text.clear()


class TodoItem(Div):
    classes: Classes = Classes("w-full flex flex-row justify-between items-center")
    remove_button: Button = Field(default_factory=lambda: Button(text=Text("Remove"), classes=Classes("btn-error")))
    page: TodoPage = PageReference()

    def __init__(self, **data):
        super().__init__(**data)
        self.remove_button.add_callback("click", self._on_click)

    async def _on_click(self):
        await self.page.todo_list.remove_item(self.text.get())


class TodoView(Div):
    classes: Classes = Classes("flex w-96 flex-col space-y-4 p-4")
    headline: Paragraph = Paragraph(text=Text("Todo List"), classes=Classes("text-2xl text-center"))
    todo_items: Collection[TodoItem] = Field(default_factory=Collection)
    page: TodoPage = PageReference()

    async def on_update(self, todo_list: TodoList):
        new_items = [
            TodoItem(
                text=Text(item),
                page=self.page,
            )
            for item in todo_list.items
        ]
        await self.todo_items.update(new_items)

    @before_render
    async def preload(self):
        self.page.todo_list.add_item.subscribe(self.on_update)
        self.page.todo_list.remove_item.subscribe(self.on_update)
        await self.on_update(self.page.todo_list)


class TodoPage(Page):
    todo_list: TodoList = Field(default_factory=TodoList)
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    input_section: InputSection = Field(default_factory=InputSection)
    todo_view: TodoView = Field(default_factory=TodoView)

    def __init__(self, **data):
        super().__init__(**data)
        inject_emitters(self.todo_list)


@app.get("/")
def get_page():
    return TodoPage()
