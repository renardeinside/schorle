class RuntimeState:
    """A class to store the runtime state of the application."""

    def __init__(self):
        self._page_context = None

    @property
    def page_context(self):
        """Returns the page context for the current thread."""
        return self._page_context

    @page_context.setter
    def page_context(self, _page):
        """Sets the page context for the current thread."""
        self._page_context = _page


def set_page_context(_page):
    """Sets the page context for the current thread."""
    rs.page_context = _page


def get_page_context():
    """Returns the page context for the current thread."""
    return rs.page_context


rs = RuntimeState()
