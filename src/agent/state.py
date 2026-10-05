from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    route: str

    # Generation output
    answer: str
    citations: list[str]

    # Retrieval information
    retrieved_chunks: list[dict[str, Any]]
    complexity: str
    retrieval_budget: int

    # Error information
    error: str | None
