import functools
import inspect
import textwrap
from functools import wraps
from typing import Callable, Optional

import tdg.extractors


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
