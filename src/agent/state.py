from typing import TypedDict


class AgentState(TypedDict, total=False):
    query: str
    answer: str
    citations: list[str]
