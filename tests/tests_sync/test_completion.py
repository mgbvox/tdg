from tdg import parsing
from tdg.agents import NavAgent
from tdg.agents.base import CodeContext
from tdg.extract import UndefinedFinder
from tdg.parsing import find_gen_signatures


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
    ingested = find_gen_signatures(something_test.__doc__)["something"]
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

    finder = UndefinedFinder(globals(), locals()).visit_code(code_example)

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


def test_nav_agent_first_pass():
    nav_agent = NavAgent(CodeContext(factorial_test))
    assert nav_agent.code_context.undefined == []
    assert len(nav_agent.code_context.signatures) == 1
    assert "def factorial(input: int) -> int:" in parsing.nl_join(
        *nav_agent.code_context.signatures
    )
