

## Before Generation
```python
@tdg
def test_asdf():
    inputs = ...
    assert list(map(asdf, inputs))
```

## After Generation

```python
### BEGIN GEN:asdf
# Gen N - mm:dd:yyyy - hh:mm:ss
# ^^ N = 1 for first generation, 2, for second, etc
def asdf(...) -> ...:
    ...
### END GEN:asdf


# On every run of this test function, log/if:
# 1. test has changed and (or?)
# 2. the test fails,
# regenerate, passing the new test and any prior failure tracebacks.
@tdg
def test_asdf():
    inputs = ...
    assert list(map(asdf, inputs))

```

We need to know which tests relate to which generated code.
If two tests both relate to one generated function, tracebacks from EACH 
should be passed into the regeneration function on fail/change.