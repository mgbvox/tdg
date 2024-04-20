import ast
from unittest import mock
from unittest.mock import patch

import pytest

from tdg import parsing
from tdg.agents import NavAgent, TestAgent
from tdg.agents.base import CodeContext, Message
from tdg.agents.dev import DevAgent
from tdg.executors.test import TestExecutor
from tdg.extract import TestFinder
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
    nav_agent = NavAgent(CodeContext(factorial_test))

    mockResponse = Message.assistant(completions.NAV_COMPLETION)

    with patch(
        "tdg.agents.nav.NavAgent._communicate_with_openai", return_value=mockResponse
    ):
        response = await nav_agent.generate()

    assert response == mockResponse


@pytest.fixture
async def nav_pre() -> NavAgent:
    nav_agent = NavAgent(CodeContext(factorial_test))

    mockResponse = Message.assistant(completions.NAV_COMPLETION)

    with patch(
        "tdg.agents.nav.NavAgent._communicate_with_openai", return_value=mockResponse
    ):
        yield nav_agent


async def test_test_agent(nav_pre):

    mockResponse = Message.assistant(completions.TEST_DESIGNER_COMPLETION)

    test_agent = TestAgent(await nav_pre.generate(), code_context=nav_pre.code_context)

    with patch(
        "tdg.agents.test.TestAgent._communicate_with_openai", return_value=mockResponse
    ):
        response = await test_agent.generate()
    assert response
    parsed, ast_or_error = is_valid_python(response.content)
    assert parsed
    assert isinstance(ast_or_error, ast.AST)


@pytest.fixture
async def tdd_agent(nav_pre):
    mockResponse = Message.assistant(completions.TEST_DESIGNER_COMPLETION)
    test_agent = TestAgent(await nav_pre.generate(), code_context=nav_pre.code_context)

    with patch(
        "tdg.agents.test.TestAgent._communicate_with_openai", return_value=mockResponse
    ):
        yield test_agent


async def test_dev_agent(tdd_agent):

    dev_agent = DevAgent(
        await tdd_agent.generate(), code_context=tdd_agent.code_context
    )

    mockResponse = Message.assistant(completions.DEVELOPER_COMPLETION)

    with patch(
        "tdg.agents.dev.DevAgent._communicate_with_openai", return_value=mockResponse
    ):
        response = await dev_agent.generate()

    assert response
    parsed, ast_or_error = is_valid_python(response.content)
    assert parsed
    assert isinstance(ast_or_error, ast.AST)


@pytest.fixture
async def dev_agent(tdd_agent):

    dev_agent = DevAgent(
        await tdd_agent.generate(), code_context=tdd_agent.code_context
    )

    mockResponse = Message.assistant(completions.DEVELOPER_COMPLETION)

    with patch(
        "tdg.agents.dev.DevAgent._communicate_with_openai", return_value=mockResponse
    ):
        yield dev_agent


async def test_test_execution(tdd_agent, dev_agent):
    solution = (await dev_agent.generate()).content
    tests = TestFinder().visit_code((await tdd_agent.generate()).content).tests.values()
    tests = list(tests)
    script = parsing.compile_tests(tests=tests, implementations=[solution], imports=[])
    ex = TestExecutor(script=script)
    await ex.test()
    assert ex.passed()
    assert ex.n_failures() == 0
