import pytest


def test_fib_base_cases():
    # Base cases defined by the user
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(3) == 2
    assert fib(4) == 3


def test_fib_large_number():
    # Test fib function with a reasonably large number to ensure efficiency
    # This value was chosen arbitrarily and may need to be adjusted based on the implementation's capabilities
    fib_result = fib(30)
    expected_result = 832040  # Known fib(30) result
    assert (
        fib_result == expected_result
    ), f"Expected {expected_result}, got {fib_result}"


def test_fib_input_validation():
    # Test fib function with invalid inputs (e.g., negative numbers, non-integer types)
    with pytest.raises(ValueError):
        fib(-1)

    with pytest.raises(TypeError):
        fib("a string")

    with pytest.raises(TypeError):
        fib(1.5)


def test_fib_zero():
    # Test how fib function handles 0, considering traditional Fibonacci sequence starts with 0 and 1
    # Expected result might differ based on implementation details
    assert (
        fib(0) == 0
    ), "Expected fib(0) to be 0 based on traditional Fibonacci sequence definition"


def test_fib_sequence_correctness():
    # Test a sequence of Fibonacci numbers to verify correctness beyond basic cases
    sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    for i, number in enumerate(sequence, start=1):
        assert fib(i) == number, f"fib({i}) should be {number}"


def test_fib_performance(benchmark):
    # Test the performance of the fib function using a fixed input
    # This uses the pytest-benchmark plugin to measure the time taken by fib(20)
    result = benchmark(fib, 20)
    assert result == 6765, "Performance test: fib(20) should return 6765"


def fib_test():
    """"""
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(3) == 2
    assert fib(4) == 3
