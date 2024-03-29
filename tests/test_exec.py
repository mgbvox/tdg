import pytest

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




