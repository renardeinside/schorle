from schorle.context_vars import RENDER_CONTROLLER


def text(content):
    element = RENDER_CONTROLLER.get().current
    element.text = content
