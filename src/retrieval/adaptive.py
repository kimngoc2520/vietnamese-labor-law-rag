def adaptive_k(complexity: float, minimum: int = 4, maximum: int = 16) -> int:
    """Choose a larger retrieval window for more complex queries."""
    return round(minimum + (maximum - minimum) * max(0.0, min(complexity, 1.0)))
