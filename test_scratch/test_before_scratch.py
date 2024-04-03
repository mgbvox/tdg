import tdg


# @tdg.gen("FileManipulator")
# def test_returns_2():
#     assert FileManipulator
#     # instantiate the manipulator
#     c = FileManipulator()
#     # find_old_files should look at a Path and return files older than a day
#     assert c.find_old_files(c.current_directory()) == []
#     # make some old files in a directory called "old" under the current dir
#     c.make_directory(name = "old", loc = c.current_directory(), with_files = [{"foo": {"created_at": "2020-01-10T00:00:00Z"}}])
#     # find those files
#     assert c.find_old_files(c.current_directory() / "old") == ["foo"]


from typing import List

def digits_of_pi(n: int) -> str:
    """
    Returns the first n digits of Pi, including the leading 3.

    Args:
    n (int): The number of digits of Pi to return, including the leading 3.

    Returns:
    str: A string representing the first n digits of Pi.
    
    Raises:
    ValueError: If n is less than 1.

    Note: This function uses the Bailey–Borwein–Plouffe (BBP) formula
    for pi to calculate the digits. It's a spigot algorithm for the
    computation of the nth hex digit of Pi, adapted here for decimal digits.
    """

    if n < 1:
        raise ValueError("Input should be a positive integer greater than 0.")
    
    pi = []
    pi.append('3')  # The leading digit in Pi

    # Skip the integer part already added
    if n == 1:
        return ''.join(pi)
    
    # Initialize variables for BBP formula
    pi_accumulator = 0
    max_j = n + 10
    for k in range(n - 1):
        k8 = 8 * k
        pi_accumulator += (4 / (k8 + 1) - 2 / (k8 + 4) - 1 / (k8 + 5) - 1 / (k8 + 6)) / (16**k)
    
    pi_digits = str(int(pi_accumulator * 10**(n-1)))  # Scale and truncate
    
    # In case of rounding errors, make sure we return exactly n digits
    pi = [pi[0]] + ['0' for _ in range(n - 1)]  # Pre-fill with zeros to ensure length
    pi[1:] = list(pi_digits)[:n-1]  # Replace starting from index 1 to n-1

    return ''.join(pi)
@tdg.gen("digits_of_pi")
def test_do_something_cool():
    assert len(str(digits_of_pi(100))) == 100
    print(digits_of_pi(100))