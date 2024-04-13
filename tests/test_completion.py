import abc
import functools
import inspect
import re
import textwrap
from typing import Callable, Any

import pytest
import yaml
from yaml.scanner import ScannerError

from tdg import parsing
from tdg.extractors.str2str import UndefinedFinder
from tests import test_root

gen_pattern = re.compile(
    r"/gen(.*?)/end[_]gen", re.DOTALL + re.MULTILINE + re.IGNORECASE
)


def dict_flat(inp: list[dict[Any, Any]]) -> dict[Any, Any]:
    """Flatten a list of dicts into one large dict."""
    return functools.reduce(lambda x, y: {**x, **y}, inp, {})


def find_gen_signatures(doc: str) -> dict[str, str]:
    """
    Extract generation context from the docstring of a test function.

    You may provide generation context in yaml format, delimited by /gen ... /endgen:

        ...random docstring contents...
        /gen
            <target_name>:
                - args:
                    - arg_1_name: arg_1_type
                    - arg_2_name: arg_2_type
                ...
        /end_gen

    Kwargs support not included (wip).

    This can be used to specify the desired structure of the object(s) to be generated.

    If this is not used, the entire docstring will be extracted for context.

    Args:
        doc: The docstring of a test function.

    """
    if not doc:
        return []
    if match := gen_pattern.search(doc):
        data = match.group(1)
        try:
            parsed = yaml.safe_load(data)
            sigs = {}
            for name, data in parsed.items():
                match data:
                    case list():
                        data = dict_flat(data)
                    case dict():
                        continue
                    case _:
                        raise TypeError(f"Unexpected value type in yaml!")
                arg_sigs = []
                for arg in data.get("args"):
                    for argname, argtype in arg.items():
                        arg_sigs.append(f"{argname}: {argtype}")

                argdef = ",".join(arg_sigs)

                fndef = f"def {name}({argdef}) -> {data.get('returns', '...')}:"
                if doc := data.get("doc"):
                    fndef = f"{fndef}\n\t'''{doc}'''"
                fndef += "\n\t..."
                fndef = parsing.format_code(fndef)

                sigs[name] = fndef

            return sigs
        except ScannerError:
            pass


def test_parse_yaml():
    loaded = yaml.safe_load((test_root / "test_gen_config.yaml").read_text())
    assert loaded


def something_test():
    """
    /gen
    something:
        - doc: A cool function.
        - args:
            - input: int
        - returns: str
    /end_gen
    """
    assert something(4) == "four"


def factorial_test():
    """
    /gen
    factorial:
        - doc: An efficient implementation of the factorial function, e.g. X!.
        - args:
            - input: int
        - returns: int
    /end_gen
    """
    assert factorial(1) == 1
    assert factorial(2) == 2 * 1
    assert factorial(3) == 3 * 2 * 1


def test_parse_doc():
    ingested = find_gen_signatures(something_test.__doc__)[0]
    target = """
    def something(input: int) -> str:
        '''A cool function.'''
        ...
    """

    assert parsing.code_eq(ingested, target)


def test_extract_undefined():
    x = 1

    # Example code string
    code_example = """
    x += 2
    a = 10
    b = a + unknown_variable
    def some_function():
        return another_undefined_variable
    """

    finder = UndefinedFinder(globals(), locals())
    finder.visit_code(code_example)

    # Find undefined objects in the example code
    assert finder.undefined == {
        "another_undefined_variable",
        "a",
        "b",
        "unknown_variable",
        "some_function",
    }


def test_extract_undefined_objects_from_code():
    assert UndefinedFinder(globals(), locals()).visit_code(
        factorial_test
    ).undefined == {"factorial"}


class Agent(abc.ABC):
    """Agent interface for multiagent generation."""

    def __init__(self, system_prompt: str):
        self.system_prompt = "\n".join(
            line.strip() for line in system_prompt.strip().splitlines()
        )


class NavAgent(Agent):
    """
    You are a Pair Programming agent in a multi-agent environment.

    Your role is "Navigator" - you look at the context and reason on a high level about what needs to be done to solve
    a given problem.

    You should NOT actually solve the problem - rather, you should provide maximally relevant context such that the
    Developer and Test Designer agents can perform their jobs optimally.
    """

    def __init__(self, test: Callable):
        super().__init__(system_prompt=NavAgent.__doc__)

        self.test = test
        self.test_source = inspect.getsource(test)
        self.test_source = self.test_source.replace(test.__doc__, "")
        self.undefined = UndefinedFinder(globals(), locals()).visit_code(test).undefined
        self.signatures = find_gen_signatures(test.__doc__)

    def _gen_prompt_first_pass(self) -> str:

        code_to_generate_chunk = []
        additional_objects = []

        for idx, undefined in enumerate(self.undefined):
            if sig := self.signatures.get(undefined):
                indented_sig = textwrap.indent(sig, "\t\t\t")
                code_to_generate_chunk.append(
                    f"\t{idx}. Function name: {undefined}\n\t\tWith signature:\n{indented_sig}"
                )
            else:
                additional_objects.append(undefined)

        gen_chunk = "\n\t".join(code_to_generate_chunk)
        additional_objects = ", ".join(additional_objects)

        prelude = "A user wants to generate some code. This code will need to pass a series of unit tests."
        targets = f"""The code to generate is:\n{gen_chunk}"""
        additional = (
            f"""The following code objects are not defined in the global
            or local context and so likely also will need to be generated:
            \n{additional_objects}"""
            if additional_objects
            else ""
        )
        tests = f"""The user has provided the following test(s) for this context:\n{self.test_source}"""

        command = (
            "Please reason in detail about what the user will need to do to solve the problem. "
            "Think in particular about any gotchas and edge cases that might be incountered."
        )

        return "\n".join([prelude, targets, additional, tests, command])


def test_nav_agent():
    nav_agent = NavAgent(factorial_test)
    assert nav_agent.undefined == {"factorial"}
    assert len(nav_agent.signatures) == 1
    assert "def factorial(input: int) -> int:" in nav_agent.signatures["factorial"]

    prompt = nav_agent._gen_prompt_first_pass()
    for name, sig in nav_agent.signatures.items():
        assert name in prompt
        for line in sig.splitlines():
            assert line.strip() in prompt


def test_dev_agent():
    pass


def test_test_agent():
    pass
