from schorle.classes import Classes
from schorle.element import button
from schorle.on import On


def Button(
    element_id: str | None = None,
    modifier: str | None = None,
    disabled: bool | None = None,
    classes: Classes | None = None,
    style: dict[str, str] | None = None,
    on: list[On] | On | None = None,
    **attributes,
) -> None:
    _classes = Classes("btn")
    if modifier:
        _classes.append(f"btn-{modifier}")
    if disabled:
        _classes.append("btn-disabled")
    if classes:
        _classes.append(classes)

    return button(element_id=element_id, classes=_classes, style=style, on=on, **attributes)
