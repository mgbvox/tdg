NAV_COMPLETION = """To solve the problem of generating a code implementation for the `factorial` function that passes the provided unit tests, the user will need to ensure the following:

1. **Correctness**: The implementation must correctly compute the factorial of a given number `n`, where `n!` is defined as the product of all positive integers less than or equal to `n`. For `n = 0`, the factorial is defined as `1`.

2. **Efficiency**: The description asks for an "efficient implementation." This typically means avoiding unnecessary computations, such as repeated calculation of factorials for numbers. A direct iterative or recursive solution can be considered, but memoization or tabulation should be utilized if the implementation leans towards recursion to enhance efficiency and avoid stack overflow errors.

3. **Edge Cases and Input Validation**:
   - The function must handle the base case of `0! = 1` according to the mathematical definition.
   - Ensure the input is a non-negative integer. Factorial is not defined for negative numbers, and handling of non-integer input should also be considered. Input validation or clear documentation should address this.
   - Consider large inputs: Depending on the language's handling of integer overflow, the user might need to take extra considerations for very large numbers, though this may not be explicitly tested in the provided unit tests.

4. **Testing Completeness**: While the user has provided a few basic tests, they should consider adding more tests to cover additional edge cases:
   - Test the base case explicitly (`factorial(0) == 1`).
   - Test with a larger number to ensure the function can handle and accurately compute larger factorials.
   - Negative input tests to ensure the function either throws an error or otherwise handles negative numbers appropriately.
   - (Optional) If the function should support large integers without overflow, tests that examine the function's ability to handle and return large numbers accurately.

5. **Documentation and Readability**: While not explicitly part of the tests, ensuring the code is well-documented and readable will help maintain and extend the implementation. This includes clear comments explaining the logic, especially if optimizations that make the code less straightforward are included.

By addressing these points, the user will develop a robust and efficient implementation of the factorial function that not only passes the provided tests but is also resilient to a broader range of inputs and scenarios.
"""


TEST_DESIGNER_COMPLETION = """
import pytest

# Tests provided by the user
def test_factorial_basic_cases():
    assert factorial(1) == 1, "Factorial of 1 should be 1"
    assert factorial(2) == 2, "Factorial of 2 should be 2"
    assert factorial(3) == 6, "Factorial of 3 should be 6"

# Additional tests to ensure coverage and edge cases
def test_factorial_zero():
    assert factorial(0) == 1, "Factorial of 0 should be 1"

def test_factorial_large_number():
    # Example testing a large number to ensure function can handle it
    assert factorial(10) == 3628800, "Factorial of 10 should be correctly computed"

def test_factorial_negative_input():
    with pytest.raises(ValueError):
        factorial(-1), "Factorial of negative numbers should raise ValueError"

def test_factorial_non_integer_input():
    with pytest.raises(TypeError):
        factorial(1.5), "Factorial of non-integer should raise TypeError"

def test_factorial_very_large_input():
    # This test is to ensure that the implementation does not run into stack overflow or take too long.
    # It is not checking for the exact correctness of the output due to the limitations on checking large numbers.
    # This test might need adjustments based on the implementation details and the environment's maximum recursion depth or integer handling.
    assert isinstance(factorial(100), int), "Factorial of very large numbers should return an integer"
    # Note: This does not assert the correctness of the output,
    # but ensures the function returns a result without error for a very large input.
"""

DEVELOPER_COMPLETION = """
def factorial(input: int) -> int:
    \"\"\"An efficient implementation of the factorial function, e.g. X!.\"\"\"
    if not isinstance(input, int):
        raise TypeError("Factorial function input must be an integer")
    if input < 0:
        raise ValueError("Factorial function input must not be negative")
    if input == 0:
        return 1
    result = 1
    for i in range(1, input + 1):
        result *= i
    return result
"""
