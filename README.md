# Test Driven Generation

A python library for AI pair programming, centered in the principles of Test Driven Development.


# Usage

Write a test, and decorate it with @tdg
```python
from my_module import my_func

@tdg
def test_my_func_for_some_case():

    some_input = 3
    some_output = 6
    assert my_func(some_input) == some_output
```

Run the test - tdg will generate code in `my_module` such that the test passes.


Specify constraints on generated code:


but wait, aren't constraints just other tests?

```python
from typing import Callable
import time

from tdg import tdg
from my_module import my_func

# by default, constraints are passed the generated function along with
def code_is_fast(fn:Callable, *args, **kwargs) -> bool:
    start = time.time_ns()
    _ = fn(*args, **kwargs)
    return time.time_ns() - start < ... # some threshold


@tdg(constraints = [code_is_fast])
def test_my_func_for_some_case():

    some_input = 3
    some_output = 6
    assert my_func(some_input) == some_output


```
