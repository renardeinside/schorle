from schorle.elements.page import Page


def test_render():
    p = Page()
    result = p.render()
    assert isinstance(result, str)
