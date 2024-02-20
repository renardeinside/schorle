from schorle.render_controller import RENDER_CONTROLLER


def text(content):
    element = RENDER_CONTROLLER.get().current
    element.text = content
