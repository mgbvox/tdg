import pytest

import tdg

pytest.main()

# For now: assume the function we're generating is the
# FIRST argument to the test function

# For now: assume we can't have groups - generate isolated code
# per test


def gen_test_fast_fib(fast_fib):
    fib_seq = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    for idx, val in enumerate(fib_seq):
        assert fast_fib(idx) == val


def test_generation_openai():
    code = tdg._gen.do_generation_openai(fn_name="fast_fib", test=gen_test_fast_fib)
    print(code)
    assert code

