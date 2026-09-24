def clamp(value: float, minimum: float, maximum: float) -> float:
    """Constrain a numeric value to an inclusive range."""
    if minimum > maximum:
        raise ValueError("minimum must not be greater than maximum.")

    return max(minimum, min(value, maximum))