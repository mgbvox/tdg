import inspect

import tdg

import pytest

pytest.main()

# For now: assume the function we're generating is the
# FIRST argument to the test function

# For now: assume we can't have groups - generate isolated code
# per test

#
# # should be a path to a module
# # will generate tests/src/gen/my_package/math.py::fast_fib
# @tdg.gen(module="my_package.math")
# def test_fast_fibonnaci(fast_fib):
#
#     # if no fast_fib implementation, generate
#     # if test has changed, should regenerate fast_fib
#     # if not, should simply import prior generated fn
#
#     fib_seq = [
#         0,
#         1,
#         1,
#         2,
#         3,
#         5,
#         8,
#         13,
#         21,
#         34,
#         55,
#         89,
#         144,
#         233,
#         377,
#         610,
#         987,
#         1597,
#         2584,
#         4181,
#     ]
#     for idx, val in enumerate(fib_seq):
#         assert fast_fib(idx) == val


def gen_test_fast_fib(fast_fib):
    fib_seq = [
        0,
        1,
        1,
        2,
        3,
        5,
        8,
        13,
        21,
        34,
        55,
        89,
        144,
        233,
        377,
        610,
        987,
        1597,
        2584,
        4181,
    ]
    for idx, val in enumerate(fib_seq):
        assert fast_fib(idx) == val


def test_generation_openai():
    code = tdg._gen.do_generation_openai(fn_name="fast_fib", test=gen_test_fast_fib)
    print(code)
    assert code


def test_foo():
    pass
