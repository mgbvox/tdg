import _ast
import ast
import inspect
import textwrap
from typing import Callable, Optional, Union, Type, TypedDict, Unpack


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


class FinderConfig(TypedDict):
    as_node: bool


class NodeSourceFinder(GenericVisitor):
    def __init__(self, *valid_types: Type[_ast.stmt], **config: Unpack[FinderConfig]):
        self.valid_types = valid_types
        self.node_sources: list[str] = []
        self.config = config
        super().__init__(self.find_node_sources)

    def find_node_sources(self, node: ast.AST):
        if any(isinstance(node, type_) for type_ in self.valid_types):
            self.node_sources.append(
                node
                if self.config.get("as_node")
                else get_node_source(self.source, node)
            )


class TestFinder(GenericVisitor):
    def __init__(self, test_prefix: str = "test_"):
        self.tests: list[str] = []
        self._test_prefix = test_prefix
        super().__init__(self.log_tests)

    def log_tests(self, node: ast.AST):
        match node:
            case ast.FunctionDef() | ast.AsyncFunctionDef():
                if node.name.startswith(self._test_prefix):
                    self.tests.append(ast.get_source_segment(self.source, node))
