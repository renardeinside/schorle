from schorle.attrs import Classes
from schorle.tags import HTMLTag
from schorle.with_attributes import WithAttributes


def test_wa():
    class WA(WithAttributes):
        tag: HTMLTag = HTMLTag.DIV
        classes: Classes = Classes("class1", "class2")

        def render(self):
            pass

    wa = WA()
    assert wa.classes.render() == "class1 class2"
