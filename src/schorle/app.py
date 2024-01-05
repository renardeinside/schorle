from typing import Dict

from loguru import logger
from starlette.responses import HTMLResponse

from schorle.elements.html import BodyClasses, BodyWithPage, EventHandler, MorphWrapper, Html
from schorle.elements.page import Page
from schorle.theme import Theme


class Schorle:
    def __init__(self, theme: Theme = Theme.DARK) -> None:
        self.routes: Dict[str, Page] = {}
        self.theme: Theme = theme

    def get(self, path: str):
        def decorator(func):
            self.routes[path] = func()
            return func

        return decorator

    def render_to_response(self, page: Page, body_class: BodyClasses = BodyWithPage) -> HTMLResponse:
        handler = EventHandler(content=page)
        body = body_class(wrapper=MorphWrapper(handler=handler))
        logger.debug(f"Rendering page: {page} with theme: {self.theme}...")
        html = Html(body=body, **{"data-theme": self.theme})
        response = HTMLResponse(html.render(), status_code=200)
        logger.debug(f"Response: {response.body.decode('utf-8')}")
        return response
