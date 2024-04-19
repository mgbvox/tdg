import inspect
from pathlib import Path

import pytest

from tdg import parsing

example = """This is some example code
```python
def function() -> int:
    return 3
```

This is also code

```python
def bar() -> float:
    print("hello")
    return 4.0
```

This aint

```yo
potato
```"""

bad_example_raw = """
def function[] -> poop:
print("hello")
"""

bad_example = f"""
This is code with syntax errors

```python
{bad_example_raw}
```
"""


def test_parses_openai_python_delimited_code():
    assert parsing.clean_openai_code_or_error(example)


def test_parses_openai_raw_python_code():
    py_fn = inspect.getsource(test_parses_openai_python_delimited_code)
    assert parsing.clean_openai_code_or_error(py_fn)


def test_raises_syntax_error_bad_delimited_code():
    with pytest.raises(SyntaxError):
        parsing.clean_openai_code_or_error(bad_example)


def test_raises_syntax_error_bad_raw_code():
    with pytest.raises(SyntaxError):
        parsing.clean_openai_code_or_error(bad_example_raw)


def test_parses_entire_file():
    assert parsing.clean_openai_code_or_error(Path(__file__).read_text())
