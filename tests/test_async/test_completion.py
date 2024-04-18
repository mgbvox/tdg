import ast
from unittest import mock
from unittest.mock import patch

import pytest

from tdg import parsing
from tdg.agents import NavAgent, TestAgent
from tdg.agents.dev import DevAgent
from tdg.executors.test import TestExecutor
from tdg.parsing import is_valid_python, nl_join
from tdg.pipeline import Pipeline
from tests import completions


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
    nav_agent = NavAgent(factorial_test)

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.NAV_PRE_COMPLETION

    with patch(
        "tdg.agents.nav.NavAgentPre._do_generation", return_value=mockCompletion
    ):
        response = await nav_agent.initial_generation()

    assert response.nav_response is not None
    assert response.nav_response != ""
    print(response.nav_response)


async def test_nav_agent_response_if_already_generated():
    nav_agent = NavAgent(factorial_test)
    nav_agent.context.nav_response = "tacos"
    assert (await nav_agent.initial_generation()).nav_response == "tacos"


@pytest.fixture
async def nav_pre() -> NavAgent:
    nav_agent = NavAgent(factorial_test)

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.NAV_PRE_COMPLETION

    with patch(
        "tdg.agents.nav.NavAgentPre._do_generation", return_value=mockCompletion
    ):
        yield nav_agent


async def test_test_agent(nav_pre):

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.TEST_DESIGNER_COMPLETION

    test_agent = TestAgent(await nav_pre.initial_generation())

    with patch("tdg.agents.test.TestAgent._do_generation", return_value=mockCompletion):
        response = await test_agent.initial_generation()
    assert response
    parsed, ast_or_error = is_valid_python(response)
    assert parsed
    assert isinstance(ast_or_error, ast.AST)
    print(response)


@pytest.fixture
async def tdd_agent(nav_pre):
    _ = await nav_pre.initial_generation()

    test_agent = TestAgent(nav_pre=nav_pre)

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.TEST_DESIGNER_COMPLETION

    with patch("tdg.agents.test.TestAgent._do_generation", return_value=mockCompletion):
        yield test_agent


async def test_dev_agent(tdd_agent):
    _ = await tdd_agent.initial_generation()

    dev_agent = DevAgent(test_agent=tdd_agent)

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.DEVELOPER_COMPLETION
    with patch("tdg.agents.dev.DevAgent._do_generation", return_value=mockCompletion):
        response = await dev_agent.initial_generation()

    assert response
    parsed, ast_or_error = is_valid_python(response)
    assert parsed
    assert isinstance(ast_or_error, ast.AST)
    print(response)


@pytest.fixture
async def dev_agent(tdd_agent):

    dev_agent = DevAgent(await tdd_agent.initial_generation())

    mockCompletion = mock.MagicMock()
    mockCompletion.choices[0].message.content = completions.DEVELOPER_COMPLETION
    with patch("tdg.agents.dev.DevAgent._do_generation", return_value=mockCompletion):
        yield dev_agent


async def test_test_execution(tdd_agent, dev_agent):
    _ = await dev_agent.initial_generation()

    ex = TestExecutor(
        script=parsing.format_code(
            nl_join(
                dev_agent.gen_response,
                tdd_agent.gen_response,
            )
        ),
    )
    ex.test()
    assert ex.passed()
