import ast
import inspect
import textwrap
from typing import Optional, Callable, Union

from tdg.parsing import parse_code


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
    return None


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


class GenericVisitor(ast.NodeVisitor):
    def __init__(self, callback: Callable[[ast.AST], None]):
        self.callback = callback

    def generic_visit(self, node: ast.AST):
        self.callback(node)
        super().generic_visit(node)

    def visit_code(self, code: Union[str, Callable]):
        if callable(code):
            code = inspect.getsource(code)
        try:
            self.visit(ast.parse(code))
            return self
        except IndentationError:
            return self.visit_code(textwrap.dedent(code))


class UndefinedFinder(GenericVisitor):
    def __init__(self, globals_: dict, locals_: dict):
        self.defined: set[str] = set()
        self.defined.update(set(globals_.keys()))
        self.defined.update(set(locals_.keys()))

        self.undefined: set[str] = set()

        super().__init__(self.log_undefined)

    def log_undefined(self, node: ast.AST):
        name = getattr(node, "name", None) or getattr(node, "id", None)
        if name and name not in self.defined:
            self.undefined.add(name)
