from typing import Any, TypedDict


class RetrievedChunk(TypedDict, total=False):
    """Shared type for a retrieved document chunk."""

    document_id: str
    chunk_index: int
    article_title: str
    content: str
    metadata: dict[str, Any]

    # Retrieval scores
    score: float
    rerank_score: float