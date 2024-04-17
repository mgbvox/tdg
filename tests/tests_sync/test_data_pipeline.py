import pytest
from _pytest.config import ExitCode

from tdg.executors.test import TestExecutor
from tdg.parsing import compile_tests
from tdg.parse_humaneval import (
    parse_hep,
    extract_prompt_name_and_doc,
    convert_tests,
    HEPItem,
)


@pytest.fixture(params=parse_hep())
def hep(request) -> HEPItem:
    """HumanEvalPlus dataset for testing."""
    return request.param


def test_extract_fn_name_and_doc(hep):
    assert hep
    fn_name, doc = extract_prompt_name_and_doc(hep)
    assert fn_name == hep.entry_point


def test_convert_tests(hep):
    if parsed := convert_tests(hep):
        solution, tests = parsed
        test_suite = compile_tests(solution, tests)
        assert test_suite
        ex = TestExecutor(test_suite)
        ex.test()
        assert ex.exit_code == ExitCode.OK
        assert ex.tracker.successes
        assert not ex.tracker.failures
