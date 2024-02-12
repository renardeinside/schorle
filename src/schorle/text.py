from schorle.context_vars import CURRENT_PARENT


def text(content):
    parent = CURRENT_PARENT.get()
    if parent is not None:
        parent.text = content
