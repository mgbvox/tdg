from typing import List


def rolling_max(numbers: List[int]) -> List[int]:
    """Generate a list of rolling maximum elements from a given list of integers."""
    if not numbers:  # Handle an empty list.
        return []
    max_list = [numbers[0]]  # Initialize the rolling max list with the first element.
    for number in numbers[1:]:
        max_list.append(
            max(number, max_list[-1])
        )  # Append the max of current element and last max.
    return max_list
