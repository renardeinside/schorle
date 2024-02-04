from __future__ import annotations

import base64
from os import PathLike
from pathlib import Path

from schorle.elements.attribute import Attribute
from schorle.elements.base.element import Element
from schorle.elements.tags import HTMLTag


class Img(Element):
    tag: HTMLTag = HTMLTag.IMG
    src: str = Attribute(..., alias="src")
    alt: str = Attribute(..., alias="alt")

    @classmethod
    def from_file(cls, path: PathLike, alt: str, mime_type: str) -> Img:
        _content = Path(path).resolve(strict=True).read_bytes()
        _encoded = base64.b64encode(_content).decode("utf-8")
        return Img(src=f"data:image/{mime_type};base64,{_encoded}", alt=alt)
