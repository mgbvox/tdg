import ast
from unittest import mock
from unittest.mock import patch

import pytest

from tdg.agents import NavAgentPre, TestAgent
from tdg.agents.dev import DevAgent
from tdg.parsing import is_valid_python
from tests.test_async import completions


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


async def test_nav_agent_response():
    nav_agent = NavAgentPre(factorial_test)

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.NAV_PRE_COMPLETION

    with patch(
        "tdg.agents.nav.NavAgentPre._do_generation", return_value=mockCompletion
    ):
        response = await nav_agent.gen()
    assert response
    print(response)


@pytest.fixture
async def nav_pre() -> NavAgentPre:
    nav_agent = NavAgentPre(factorial_test)

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.NAV_PRE_COMPLETION

    with patch(
        "tdg.agents.nav.NavAgentPre._do_generation", return_value=mockCompletion
    ):
        yield nav_agent


async def test_test_agent(nav_pre):
    _ = await nav_pre.gen()

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.TEST_DESIGNER_COMPLETION

    test_agent = TestAgent(nav_pre=nav_pre)

    with patch("tdg.agents.test.TestAgent._do_generation", return_value=mockCompletion):
        response = await test_agent.gen()
    assert response
    parsed, ast_or_error = is_valid_python(response)
    assert parsed
    assert isinstance(ast_or_error, ast.AST)
    print(response)


@pytest.fixture
async def tdd_agent(nav_pre):
    _ = await nav_pre.gen()

    test_agent = TestAgent(nav_pre=nav_pre)

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.TEST_DESIGNER_COMPLETION

    with patch("tdg.agents.test.TestAgent._do_generation", return_value=mockCompletion):
        yield test_agent


async def test_dev_agent(tdd_agent):
    old = await tdd_agent.gen()

    dev_agent = DevAgent(test_agent=tdd_agent)

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.DEVELOPER_COMPLETION
    with patch("tdg.agents.dev.DevAgent._do_generation", return_value=mockCompletion):
        response = await dev_agent.gen()

    assert response
    parsed, ast_or_error = is_valid_python(response)
    assert parsed
    assert isinstance(ast_or_error, ast.AST)
    print(response)
