import ast
import textwrap
from typing import Union


def parse_code(code: str) -> ast.AST:
    """Parse a code string into a Python AST."""
    return ast.parse(textwrap.dedent(code))


def dump_ast(node: ast.AST) -> str:
    """Dump an ast node using the standard indent of 4 spaces."""
    return ast.dump(node, indent=4)


def code_eq(a: str, b: str) -> bool:
    """Compare two code strings for functional equivalence by parsing their abstract syntax trees."""
    a_parsed = dump_ast(parse_code(a))
    b_parsed = dump_ast(parse_code(b))

    return a_parsed == b_parsed


def is_valid_python(code: str) -> tuple[bool, Union[ast.AST, SyntaxError]]:
    try:
        parsed = ast.parse(code)
        return True, parsed
    except SyntaxError as e:
        return False, e
