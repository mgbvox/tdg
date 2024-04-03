import functools
import inspect
import textwrap
from typing import Callable, Optional

import tdg.extractors
from tdg.extractors import find_definition, code_eq


class some_decorator_class:
    def __init__(self, fn: Optional[Callable] = None):
        if fn:
            self.fn = fn
            functools.update_wrapper(self, fn)

    def __call__(self, *args, **kwargs):
        if args and callable(args[0]):
            functools.update_wrapper(self, args[0])
            return args[0]
        else:
            return self.fn(*args, **kwargs)


BASIC_TARGET = "Hello, world!"


# with ()
@some_decorator_class()
def foo():
    return BASIC_TARGET


# without ()
@some_decorator_class
def bar():
    return BASIC_TARGET


def test_decorator_return():
    assert foo() == BASIC_TARGET

    assert bar() == BASIC_TARGET
    print(inspect.getsource(bar))


def test_rm_decorator_basic():
    without_decorator = textwrap.dedent(
        """
    def {name}():
        return BASIC_TARGET
    """
    ).strip()
    extracted = tdg.extractors.strip_decorator(foo)
    assert extracted == without_decorator.format(name="foo")

    extracted = tdg.extractors.strip_decorator(bar)
    assert extracted == without_decorator.format(name="bar")


def test_find_definition():

    # Example usage
    code = """
    x = 5
    def foo():
        pass
    class Bar:
        def __init__(self, x:int):
            self.x = x
        
        def woot(self):
            print(self.x)
    """

    target = """
        def foo():
            pass
        """

    definition = find_definition(code, "foo")
    assert code_eq(definition, target)

    target = """
    class Bar:
        def __init__(self, x:int):
            self.x = x
        
        def woot(self):
            print(self.x)
    """
    definition = find_definition(code, "Bar")
    assert code_eq(definition, target)

    definition = find_definition(code, "x")
    assert code_eq(definition, "x = 5")

    definition = find_definition(code, "self.x")
    assert definition is None
