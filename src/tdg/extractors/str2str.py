import ast
import inspect
import textwrap
from typing import Optional, Callable, Union


def find_definition(code: str, name: str) -> Optional[str]:
    """
    Given a code string, return the portion of the code string that defines a code object with the given name.

    Args:
        code: The code string.
        name: The name of the code object definition to return.

    Returns:
        Optional[str]: The portion of the code that defines `name`, or `None` if no definition exists.
    """

    return DefinitionFinder(name).visit_code(code).definition_source


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


class GenericVisitor(ast.NodeVisitor):
    def __init__(self, callback: Callable[[ast.AST], None]):
        self.callback = callback
        self.source: Optional[str] = None
        self.ast: Optional[ast.AST] = None

    def generic_visit(self, node: ast.AST):
        self.callback(node)
        super().generic_visit(node)

    def visit_code(self, code: Union[str, type, Callable]):
        if not isinstance(code, str):
            code = inspect.getsource(code)

        try:
            self.source = code
            parsed = ast.parse(code)
            self.ast = parsed
            self.visit(parsed)
            return self
        except IndentationError:
            return self.visit_code(textwrap.dedent(code))


class DefinitionFinder(GenericVisitor):
    def __init__(self, name):
        self.name = name
        self.definition = None
        super().__init__(self.find_definition)

    def find_definition(self, node: ast.AST):
        if getattr(node, "name", getattr(node, "id", "")) == self.name:
            self.definition = node

    @property
    def definition_source(self) -> Optional[str]:
        if self.source and self.definition:
            return ast.get_source_segment(self.source, self.definition)


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
