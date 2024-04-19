import pytest
from _pytest.config import ExitCode

from tdg.agents import NavAgent
from tdg.agents.base import CodeContext
from tdg.executors.test import TestExecutor
from tdg.parse_humaneval import (
    parse_hep,
    convert_tests,
    HEPItem,
)

N = -1


@pytest.fixture(params=parse_hep()[:N])
def hep(request) -> HEPItem:
    """HumanEvalPlus dataset for testing."""
    return request.param


def test_code_context_from_hep(hep):
    if hep_suite := convert_tests(hep):

        train, test = hep_suite.split(10)
        assert len(train.tests) == 10
        assert len(hep_suite.tests) == len(train.tests) + len(test.tests)

        assert CodeContext(train)
        assert CodeContext(test)
        assert CodeContext(hep_suite)

        nav = NavAgent(CodeContext(train))
        assert nav.user_prompt()
        assert nav.system_prompt()


def test_convert_tests(hep):
    if parsed := convert_tests(hep):
        subset, _ = parsed.split(10)
        ex = TestExecutor(subset.compile())
        ex.test()
        assert ex.exit_code == ExitCode.OK
        assert ex.tracker.successes
        assert not ex.tracker.failures
