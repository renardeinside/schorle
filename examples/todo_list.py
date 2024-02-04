from __future__ import annotations

from pydantic import Field

from schorle.app import Schorle
from schorle.effector import effector
from schorle.elements.base.element import Collection, Reactive
from schorle.elements.button import Button
from schorle.elements.html import Div
from schorle.elements.inputs import Input
from schorle.elements.page import Page, PageReference
from schorle.reactives.classes import Classes
from schorle.reactives.state import ReactiveModel
from schorle.reactives.text import Text

app = Schorle()


class TodoList(ReactiveModel):
    items: list[str] = Field(default_factory=lambda: ["Buy milk", "Buy eggs", "Buy bread"])

    @effector
    async def add_item(self, item: str):
        self.items.append(item)

    @effector
    async def remove_item(self, item: str):
        self.items.remove(item)


class InputSection(Div):
    classes: Classes = Classes("flex flex-row justify-center items-center w-6/12 space-x-4")
    input_text: Input = Input(placeholder="Enter text here")
    add_button: Button = Button(text="Add", classes=Classes("btn-primary"))
    page: TodoPage = PageReference()

    async def before_render(self):
        self.add_button.add_callback("click", self._on_click)

    async def _on_click(self):
        new_input = self.input_text.value.get()
        if new_input:
            await self.page.todo_list.add_item(new_input)
            await self.input_text.clear()


class TodoItem(Div):
    classes: Classes = Classes("w-full flex flex-row justify-between items-center")
    remove_button: Button = Button.factory(text=Text("Remove"), classes=Classes("btn-error"))
    page: TodoPage = PageReference()

    async def before_render(self):
        self.remove_button.add_callback("click", self._on_click)

    async def _on_click(self):
        await self.page.todo_list.remove_item(self.text.get())


class TodoView(Div):
    classes: Classes = Classes("flex w-96 flex-col space-y-4 p-4")
    headline: Reactive[Div] = Reactive.factory()
    todo_items: Collection[TodoItem] = Collection.factory()
    page: TodoPage = PageReference()

    async def update_items(self, todo_list: TodoList):
        async with self.suspend():
            new_items = [TodoItem(text=Text(item)) for item in todo_list.items]
            await self.todo_items.update(new_items)

    async def update_headline(self, todo_list: TodoList):
        _text = (
            f"Todo List with {len(todo_list.items)} item{'s' if len(todo_list.items) > 1 else ''}"
            if todo_list.items
            else "Todo List is empty"
        )
        await self.headline.update(Div(text=Text(_text), classes=Classes("text-2xl")))

    async def before_render(self):
        for updater in [self.update_items, self.update_headline]:
            await self.page.todo_list.add_item.subscribe(updater, trigger=True)
            await self.page.todo_list.remove_item.subscribe(updater, trigger=True)


class TodoPage(Page):
    todo_list: TodoList = TodoList.factory()
    classes: Classes = Classes("flex flex-col justify-center items-center h-screen w-screen")
    input_section: InputSection = InputSection.factory()
    todo_view: TodoView = TodoView.factory()


@app.get("/")
def get_page():
    return TodoPage()
