def estimate_complexity(query: str) -> float:
    words = len(query.split())
    return max(0.0, min(words / 40, 1.0))
