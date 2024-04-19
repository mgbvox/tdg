import functools
import inspect
import textwrap
from pathlib import Path
from typing import Callable, Optional

from tdg.executors.test import TestExecutor
from tdg.extract import strip_decorator, find_definition

from tdg import parsing
from tdg.parsing import code_eq
from tests import completions


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
    extracted = strip_decorator(foo)
    assert extracted == without_decorator.format(name="foo")

    extracted = strip_decorator(bar)
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


def test_extract_test_source():
    source = Path(__file__).parent / "extractor_data" / "demo_test_suite.txt"
    source = source.read_text()

    tests = parsing.extract_tests(source)
    assert len(tests) == 5


def test_filter_imports():

    good = [
        # import third party
        "import pydantic",
        # import this package
        "import tdg",
        # import submodule
        "from pydantic import BaseModel",
        # dotted import from
        "from pydantic.config import BaseConfig",
        # this package dotted import from
        "from tdg.config import Settings",
        # dotted comma import from
        "from tdg.parsing import extract_imports, extract_tests",
        # multiline dotted comma import from
        textwrap.dedent(
            """
            from tdg.parsing import (
            extract_imports,
            extract_tests,
            )
            """
        ),
    ]

    bad = [
        # bad module
        "import bad_doesnt_exist",
        # bad syntax
        "1234 I am _ not code",
        # good module, bad submodule
        "from tdg import whoops",
        # dotted module.submodule, bad attribute
        "from tdg.parsing import oh_no",
        # comma imports, one is bad
        "from tdg.parsing import extract_imports, extract_tacos, extract_tests",
        # multiline import
        textwrap.dedent(
            """
            from tdg.parsing import (
            extract_imports,
            extract_tests,
            extract_tacos,
            )
            """
        ),
    ]

    found_good, found_bad = parsing.filter_imports(*(good + bad))

    assert sorted(found_bad) == sorted(bad)
    assert sorted(found_good) == sorted(good)


def test_extract_test_source_filter_valid_imports():
    source = Path(__file__).parent / "extractor_data" / "demo_test_suite.txt"
    source = source.read_text()

    imports, _ = parsing.extract_and_filter_imports(source)
    tests = parsing.extract_tests(source)
    script = parsing.compile_tests(
        tests, imports=imports, implementations=[completions.DEVELOPER_COMPLETION]
    )

    tested = TestExecutor(script=script).test()
    assert tested.passed()
