from fastapi import APIRouter

from src.api.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    return FeedbackResponse(
        status="accepted",
        message="Feedback received.",
    )