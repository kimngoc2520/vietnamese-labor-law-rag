def reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """Combine ranked result lists using reciprocal rank fusion."""
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for results in result_lists:
        for rank, item in enumerate(results, start=1):
            key = str(item.get("id", item.get("content", rank)))
            scores[key] = scores.get(key, 0.0) + 1 / (k + rank)
            items[key] = item
    return sorted(items.values(), key=lambda item: scores[str(item.get("id", item.get("content")))], reverse=True)
