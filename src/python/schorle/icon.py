from schorle.element import icon as html_icon


def icon(name: str):
    html_icon(attrs={"data-lucide": name})
