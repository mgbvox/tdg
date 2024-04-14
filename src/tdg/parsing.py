import ast
import functools
import re
import textwrap
from typing import Union, Any

import black
import yaml
from yaml.scanner import ScannerError


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


def compile_tests(solution: str, tests: list[str]) -> str:
    script = "\n".join([solution] + tests)
    script = format_code(script)
    return script


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

        ...random docstring contents...
        /gen
            <target_name>:
                - args:
                    - arg_1_name: arg_1_type
                    - arg_2_name: arg_2_type
                ...
        /end_gen

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
