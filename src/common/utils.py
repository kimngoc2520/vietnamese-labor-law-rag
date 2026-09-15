def clamp(value: float, minimum: float, maximum: float) -> float:
    """Constrain a numeric value to an inclusive range."""
    return max(minimum, min(value, maximum))
