import tdg


@tdg.gen("returns_2")
def test_returns_2():
    assert returns_2() == 2
