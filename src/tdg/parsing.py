import _ast
import ast
import functools
import importlib
import importlib.util
import re
import textwrap
from pathlib import Path
from typing import Union, Any, Type, Unpack

import black
import yaml
from yaml.scanner import ScannerError

from tdg.extract import NodeSourceFinder, FinderConfig, TestFinder


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
    except Exception as e:
        raise ValueError(
            f"Unable to parse input code, and it wasn't a syntax issue.\ncode:\n{code}"
        ) from e


def format_code(code: str) -> str:
    return black.format_str(code, mode=black.Mode())


def compile_tests(
    tests: list[str],
    *,
    imports: list[str] = None,
    implementations: list[str] = None,
) -> str:
    imports = imports or ["import pytest"]
    implementations = implementations or []
    script = nl_join(*imports, *implementations, *tests)
    script = format_code(script)
    return script


@functools.lru_cache(None)
def _extract_nodes(
    code: Union[str, Path],
    *types_: Type[_ast.stmt],
    **kwargs: Unpack[FinderConfig],
) -> list[str]:
    if isinstance(code, Path):
        code = code.read_text()
    finder = NodeSourceFinder(*types_, **kwargs).visit_code(code)
    return finder.node_sources


def extract_imports(code: str, **kwargs: Unpack[FinderConfig]) -> list[str]:
    return _extract_nodes(
        code,
        ast.Import,
        ast.ImportFrom,
        **kwargs,
    )


def extract_and_filter_imports(
    code: str, invert: bool = False
) -> tuple[list[str], list[str]]:
    return filter_imports(*extract_imports(code), invert=invert)


@functools.lru_cache(None)
def filter_imports(*imports: str, invert: bool = False) -> tuple[list[str], list[str]]:
    """Given a list of import statements, return only the statements that import from
    modules in the current interpreter path.

    Args:
    imports (list[str]): A list of import statements as strings.
    invert: If true, return only the statements that are invalid as imports.

    Returns:
    list[str], list[str]: Two lists. First is valid imports, second is invalid imports.
    """
    filtered_imports = set()
    invalid_imports = set()

    for import_statement in imports:
        try:
            # Parse the import statement into an AST
            parsed = extract_imports(import_statement, as_node=True)
        except SyntaxError:
            # If parsing fails, log as invalid and skip this statement
            invalid_imports.add(import_statement)
            continue

        # Loop through the body of the parsed AST
        for node in parsed:
            # map module names to any imported submodules
            modules_map = {}

            if isinstance(node, ast.Import):
                # (no_package, module)
                for alias in node.names:
                    modules_map[alias.name] = []
            elif isinstance(node, ast.ImportFrom):
                # (package, module)
                modules_map[node.module] = [alias.name for alias in node.names]

            else:
                continue  # Skip any non-import statements

            # Check if these modules can be found by the interpreter

            for key, values in modules_map.items():
                # if importlib.util.find_spec(module_name) is not None:
                try:
                    module = importlib.import_module(key)
                    if values:
                        for value in values:
                            try:
                                _ = getattr(module, value)
                            except AttributeError:
                                raise ModuleNotFoundError(
                                    f"Module {key} has no attribute {value}"
                                )
                    # if we've gotten this far, the module, and all submodules (if any),
                    # are importable - add this as a valid import statement!
                    filtered_imports.add(import_statement)

                except ModuleNotFoundError:
                    # import not available in current namespace; is invalid
                    invalid_imports.add(import_statement)

    return sorted(list(filtered_imports)), sorted(list(invalid_imports))


def extract_tests(
    code: Union[str, Path],
) -> list[str]:
    return list(TestFinder().visit_code(code).tests.values())


gen_pattern = re.compile(
    r"/gen(.*?)/end[_]gen", re.DOTALL + re.MULTILINE + re.IGNORECASE
)


def dict_flat(inp: list[dict[Any, Any]]) -> dict[Any, Any]:
    """Flatten a list of dicts into one large dict."""
    return functools.reduce(lambda x, y: {**x, **y}, inp, {})


def find_gen_signatures(doc: str) -> dict[str, str]:
    """
    Extract generation context from the docstring of a test function.

    You may provide generation context in yaml format, delimited by /gen ... /endgen:

    def test_some_function():
        '''
        /gen
            <target_name>:
                - doc: <natural language description of target function>
                - args:
                    - arg_1_name: arg_1_type
                    - arg_2_name: arg_2_type
                ...
        /end_gen
        '''

    Kwargs support not included (wip).

    This can be used to specify the desired structure of the object(s) to be generated.

    If this is not used, the entire docstring will be extracted for context.

    Args:
        doc: The docstring of a test function.

    """
    if not doc:
        return {}
    if match := gen_pattern.search(doc):
        data = match.group(1)
        try:
            parsed = yaml.safe_load(data)
            sigs = {}
            for name, data in parsed.items():
                match data:
                    case list():
                        data = dict_flat(data)
                    case dict():
                        continue
                    case _:
                        raise TypeError("Unexpected value type in yaml!")
                arg_sigs = []
                for arg in data.get("args"):
                    for argname, argtype in arg.items():
                        arg_sigs.append(f"{argname}: {argtype}")

                argdef = ",".join(arg_sigs)

                fndef = f"def {name}({argdef}) -> {data.get('returns', '...')}:"
                if doc := data.get("doc"):
                    fndef = f"{fndef}\n\t'''{doc}'''"
                fndef += "\n\t..."
                fndef = format_code(fndef)

                sigs[name] = fndef

            return sigs
        except ScannerError:
            pass
    return {}


python_pattern = re.compile(r"```python(.*?)```", re.DOTALL + re.MULTILINE)


def clean_openai_code_or_error(code: str) -> str:
    """
    Extract all code (delimited by ```python```) from an openai generation string.

    If multiple code blocks are provided, they will be sequentially joined.

    Output is passed through the black formatter and parsed to ensure functionality.

    Args:
        code: The raw input string to parse.

    Returns:

    """
    if matches := python_pattern.findall(code):
        extracted = nl_join(*matches)
    else:
        # assume the input is already valid python code
        extracted = code

    parsed, ast_or_error = is_valid_python(extracted)
    if parsed:
        return format_code(extracted)

    else:
        raise SyntaxError(
            nl_join(
                "Invalid python code generated!",
                code,
            )
        ) from ast_or_error


def nl_join(*args: str) -> str:
    return "\n".join(args)
