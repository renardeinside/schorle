import base64
import hashlib
from pathlib import Path
from typing import List, Optional

from schorle.theme import Theme


def _get_integrity_hash(bundle):
    _b64_bytes = base64.b64encode(hashlib.sha384(bundle).digest())
    sha = "sha384-" + _b64_bytes.decode("utf-8")
    return sha


# _bundle = pkgutil.get_data("schorle", "assets/bundle.js")
# _integrity_hash = _get_integrity_hash(_bundle)


class Schorle:
    def __init__(self, theme: Optional[Theme] = "dark", css_extras: List[Path] | None = None) -> None:
        self.routes = {}
        self.theme = theme
        self.css_extras = css_extras

    def route(self, path: str):
        """Decorator to register a function as a route handler."""

        def decorator(func):
            self.routes[path] = func
            return func

        return decorator
