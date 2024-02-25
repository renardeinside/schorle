from fastapi import UploadFile
from loguru import logger

from schorle.app import Schorle
from schorle.attrs import Classes, On
from schorle.element import div
from schorle.inputs import FileInput
from schorle.page import Page
from schorle.state import ReactiveModel, Ref, effector
from schorle.text import text

app = Schorle()


class State(ReactiveModel):
    file_content: str | None = None

    @effector
    async def on_change(self, file: UploadFile):
        _data = await file.read()
        self.file_content = _data.decode("utf-8")


class TableViewerPage(Page):
    classes: Classes = Classes("p-4 flex flex-col justify-center items-center h-screen")
    state: State = State.factory()
    input_ref: Ref[FileInput] = Ref()

    async def on_change(self, file: UploadFile):
        logger.info(f"Received file: {file.filename}")
        await self.input_ref.current.clear()
        await self.state.on_change(file)

    def render(self):
        if self.state.file_content:
            with div(classes=Classes("w-1/2", "h-1/2", "overflow-auto")):
                text(self.state.file_content)
        else:
            FileInput(
                classes=Classes("input-bordered", "input-secondary"),
                on=On("change", self.on_change),
                ref=self.input_ref,
            )

    def initialize(self):
        self.bind(self.state)


@app.get("/")
def home():
    return TableViewerPage()
