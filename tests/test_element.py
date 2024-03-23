from schorle.attrs import Classes
from schorle.element import div


def test_el():
    with div() as d:
        d.div().text("hey")

    assert d.render(pretty_print=False) == "<div><div>hey</div></div>"

    with div() as d:
        d.div().text("hey")
        d.div().text("ho")

    assert d.render(pretty_print=False) == "<div><div>hey</div><div>ho</div></div>"


def test_with_attrs():
    with div(element_id="level1") as d:
        d.div(element_id="level2").text("hey")

    assert d.render(pretty_print=False) == '<div id="level1"><div id="level2">hey</div></div>'

    with div(element_id="level1", classes=Classes("bg-red-500")) as d:
        d.div(element_id="level2").text("hey")

    assert d.render(pretty_print=False) == '<div id="level1" class="bg-red-500"><div id="level2">hey</div></div>'
