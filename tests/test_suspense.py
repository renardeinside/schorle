from loguru import logger
from lxml import etree

from schorle.controller import RenderController
from schorle.element import div
from schorle.loading import Loading
from schorle.state import Reactive
from schorle.suspense import Suspense


def test_loading():
    loading = Loading()
    rm = Reactive[str](value="hey")

    suspense = Suspense(on=rm, fallback=loading)
    parent = div(element_id="hey")
    suspense.parent = parent

    def combined():
        with suspense.parent():
            suspense.fallback()

    with RenderController() as rc:
        result = rc.render(combined)
        logger.debug(etree.tostring(result, pretty_print=True).decode())
