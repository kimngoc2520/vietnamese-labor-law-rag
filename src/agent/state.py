from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    route: str
    answer: str
    citations: list[str]
    retrieved_chunks: list[dict[str, Any]]