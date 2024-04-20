from typing import List


def parse_nested_parens(paren_string: str) -> List[int]:
    """Parses a string of parentheses groups and calculates the
    maximum depth of parentheses nesting for each group."""
    # Split the string into groups of parentheses
    groups = paren_string.split()
    max_depths = []

    for group in groups:
        max_depth = 0
        current_depth = 0
        for char in group:
            if char == "(":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ")":
                current_depth -= 1
        max_depths.append(max_depth)

    return max_depths
