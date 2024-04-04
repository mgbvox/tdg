import inspect
import textwrap
from typing import Callable


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
