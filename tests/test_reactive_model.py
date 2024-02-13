from schorle.effector import effector
from schorle.reactives.state import ReactiveModel


def test_rm():
    class Counter(ReactiveModel):
        value: int = 0

        @effector
        def increment(self):
            self.value += 1

    c = Counter()
    assert c.value == 0
    c.increment.subscribe(lambda: print("incremented"))
    c.increment()
    assert c.value == 1
