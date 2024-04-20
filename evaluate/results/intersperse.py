from typing import List


def intersperse(numbers: List[int], delimiter: int) -> List[int]:
    """Inserts a given delimiter between every two consecutive elements in the list."""
    if not numbers:
        return []
    result = [numbers[0]]
    for number in numbers[1:]:
        result.append(delimiter)
        result.append(number)
    return result
