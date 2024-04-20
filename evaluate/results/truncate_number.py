def truncate_number(number: float) -> float:
    if number < 0:
        raise ValueError("Input must be a non-negative number")
    return number - int(number)
