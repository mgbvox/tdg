import ast
import inspect
import textwrap
from typing import Callable, Optional, Union


def strip_decorator(func: Callable) -> str:
    # Get the source code of the function including decorators
    source_code_with_decorators = inspect.getsource(func)

    # Process the source to remove decorator lines
    source_lines = source_code_with_decorators.splitlines()
    # Find the first line that does not start with @ (assumes decorators start with @)
    first_non_decorator_line_index = next(
        i for i, line in enumerate(source_lines) if not line.strip().startswith("@")
    )
    # Join the remaining lines to get the body without decorators
    body_without_decorators = textwrap.dedent(
        "\n".join(source_lines[first_non_decorator_line_index:])
    )

    return body_without_decorators.strip()


class DefinitionFinder(ast.NodeVisitor):
    def __init__(self, name):
        self.name = name
        self.definition = None

    def visit_FunctionDef(self, node):
        if node.name == self.name:
            self.definition = node
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if node.name == self.name:
            self.definition = node
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if node.name == self.name:
            self.definition = node
        self.generic_visit(node)

    def visit_Assign(self, node):
        # Handle variable assignment. Variables can be assigned in different ways,
        # e.g., a single name or a tuple of names. This is a simple example.
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == self.name:
                self.definition = node
        self.generic_visit(node)


def get_node_source(code: str, node: ast.AST) -> str:
    """
    Extracts the source code segment for the given AST node and all its children.
    """
    lines = textwrap.dedent(code).splitlines()
    start_line = node.lineno - 1  # 1-based indexing in AST to 0-based in Python lists
    end_line = getattr(
        node, "end_lineno", start_line + 1
    )  # Use end_lineno if available, otherwise guess

    # Capture the start and end of the node including all its children
    node_source = lines[start_line:end_line]

    # If available, adjust the ending to include the correct column offset
    if hasattr(node, "end_col_offset") and node_source:
        node_source[-1] = node_source[-1][: node.end_col_offset]

    return "\n".join(node_source)


def find_definition(code: str, name: str) -> Optional[str]:
    """
    Given a code string, return the portion of the code string that defines a code object with the given name.

    Args:
        code: The code string.
        name: The name of the code object definition to return.

    Returns:
        Optional[str]: The portion of the code that defines `name`, or `None` if no definition exists.
    """
    ast_module = parse_code(code)
    finder = DefinitionFinder(name)
    finder.visit(ast_module)
    if definition := finder.definition:
        return get_node_source(code, definition)


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
