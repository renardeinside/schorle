from __future__ import annotations

import base64
from os import PathLike
from pathlib import Path

from pydantic import model_validator

from schorle.attribute import Attribute
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag


class Img(Element):
    tag: HTMLTag = HTMLTag.IMG
    src: str | None = Attribute(None, alias="src")
    alt: str = Attribute(..., alias="alt")
    file_path: PathLike | None = None
    mime_type: str | None = None

    @model_validator(mode="after")
    def check_file_path_and_mime_type(self):
        if self.file_path and self.src:
            raise ValueError("You can only set either file_path or src, not both.")
        if not self.file_path and not self.src:
            raise ValueError("You must set either file_path or src.")
        if self.file_path and not self.mime_type:
            raise ValueError("You must set mime_type when using file_path.")
        if self.file_path and self.mime_type:
            self.src = self._from_file(self.file_path, self.mime_type)

        return self

    @classmethod
    def _from_file(cls, path: PathLike, mime_type: str) -> str:
        _content = Path(path).resolve(strict=True).read_bytes()
        _encoded = base64.b64encode(_content).decode("utf-8")
        _src = f"data:{mime_type};base64,{_encoded}"
        return _src
