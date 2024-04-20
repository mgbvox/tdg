from typing import List


def filter_by_substring(strings: List[str], substring: str) -> List[str]:
    if not substring:  # Correct check for an empty substring to return an empty list
        return []  # Correct action when substring is empty
    return [s for s in strings if substring in s]
