from schorle.classes import Classes
from schorle.element import span
from schorle.text import text


def dev_loading_spinner():
    with span(
        element_id="schorle-loading-indicator",
        classes=Classes(
            "loading",
            "loading-lg",
            "text-info",
            "loading-infinity",
            "fixed",
            "right-2",
            "bottom-2",
        ),
    ):
        text("")
