import pytest

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


@pytest.mark.asyncio
async def test_full_pipeline():
    pipeline = Pipeline(factorial_test, from_id="a2afd9d3-0c60-4b13-b6d7-84efaf49d4dc")
    out = await pipeline.gen()
    assert out
