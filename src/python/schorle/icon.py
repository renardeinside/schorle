from schorle.element import Element
from schorle.element import icon as html_icon


def icon(name: str) -> Element:
    return html_icon(attrs={"data-lucide": name})
