import inspect
import textwrap
from typing import Callable

import pytest

from tdg import parsing
from tdg.pipeline import Pipeline


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


factorial = None


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


def factorial_test_w_pass_in(factorial: Callable[[int], int]):
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


@pytest.mark.asyncio
async def test_full_pipeline():
    pipeline = Pipeline(factorial_test, from_id="a2afd9d3-0c60-4b13-b6d7-84efaf49d4dc")
    out = await pipeline.gen()
    assert out
    compiled_code = compile(out, "<string>", "exec")
    local_namespace = {}
    exec(compiled_code, local_namespace)
    factorial = local_namespace["factorial"]
    factorial_test_w_pass_in(factorial)


@pytest.mark.asyncio
async def test_full_pipeline_with_failing_initial_impl():
    pipeline = Pipeline(factorial_test, from_id="a2afd9d3-0c60-4b13-b6d7-84efaf49d4dc")
    await pipeline.gen(no_test=True)

    def factorial(input: int) -> int:
        return input

    bad_implementation = textwrap.dedent(inspect.getsource(factorial))
    pipeline.dev.history.alter_initial(bad_implementation)
    assert (
        pipeline.dev.history.initial_response.content
        in pipeline.dev.history.messages[2].content
    )
    assert pipeline.dev.history.initial_response.content == bad_implementation
    assert pipeline.dev.history.initial_response.role == "assistant"
    assert len(pipeline.dev.history.messages) == 3

    fixed = await pipeline.test_until_passing(solution=bad_implementation, depth=0)
    assert pipeline.tester.passed()

    compiled_code = compile(fixed, "<string>", "exec")
    local_namespace = {}
    exec(compiled_code, local_namespace)
    factorial_fixed = local_namespace["factorial"]
    factorial_test_w_pass_in(factorial_fixed)
