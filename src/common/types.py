from typing import TypedDict


class RetrievedChunk(TypedDict):
    content: str
    score: float
    source: str
