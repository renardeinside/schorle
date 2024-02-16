import base64
from pathlib import Path

from schorle.classes import Classes
from schorle.element import img
from schorle.on import On


def Image(
    src: str | Path,
    alt: str,
    media_type: str | None = None,
    element_id: str | None = None,
    classes: Classes | None = None,
    style: dict[str, str] | None = None,
    on: list[On] | On | None = None,
    **attributes,
) -> None:
    if isinstance(src, Path):
        if not media_type:
            raise ValueError("media_type must be provided when src is a Path object")

        _src = f"data:{media_type};base64,{base64.b64encode(src.read_bytes()).decode()}"
    else:
        _src = src

    attributes["src"] = _src
    attributes["alt"] = alt

    return img(element_id=element_id, classes=classes, style=style, on=on, **attributes)
