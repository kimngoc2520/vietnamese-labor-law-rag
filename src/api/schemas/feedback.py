from typing import Literal

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1)
    rating: Literal["positive", "negative"]
    comment: str | None = None


class FeedbackResponse(BaseModel):
    status: str
    message: str