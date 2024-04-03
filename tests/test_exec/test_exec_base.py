import pytest

from tdg.executors.base import Executor

basic = """
x += 1
y = x * 2
"""


def test_exec():
    x = 3
    globals_dict = {"x": x}
    exec(basic, globals_dict)
    # Now check the 'x' inside globals_dict
    assert globals_dict["x"] == 4


test_fn_2 = """
assert some_fn() == 2
"""


def test_can_pass_code_obj_to_globals():
    exec(test_fn_2, {"some_fn": lambda: 2})
    with pytest.raises(AssertionError):
        exec(test_fn_2, {"some_fn": lambda: 3})


def test_exec_class_builtins_local_mutability():
    # global x
    x = 3

    # exec on inner local x
    e = Executor(x=1)
    e.run("x += 1")
    # mutates inner x
    assert e.x == 2
    # global x unaffected
    assert e.x != x

    with pytest.raises(SyntaxError):
        e.run("1 = not valid")


def test_exec_class_class_stuff():

    class Boop:
        def __init__(self, a: str):
            self.a = a

    # should not be affected by .run ops
    b = Boop("asdf")

    e = Executor(b=b)
    e.run("b.a += 'eyo'")

    # inner env remains modified
    assert e.b.a == "asdfeyo"

    # outer b obj not modified
    assert b.a == "asdf"
