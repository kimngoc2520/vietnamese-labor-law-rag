from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question")


class ChatResponse(BaseModel):
    query: str
    answer: str
    citations: list[str]
    complexity: str
    retrieval_budget: int