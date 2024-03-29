import tdg


def returns_2() -> int:
    return 2


@tdg.gen
def test_returns_2():
    assert returns_2() == 2
