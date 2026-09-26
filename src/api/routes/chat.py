from fastapi import APIRouter, HTTPException

from src.api.schemas.chat import ChatRequest, ChatResponse
from src.generation.pipeline import GenerationPipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query must not be empty.",
        )

    try:
        pipeline = GenerationPipeline()
        result = pipeline.run(query=query)

        return ChatResponse(
            query=query,
            answer=result.answer,
            citations=result.citations,
            complexity=result.complexity,
            retrieval_budget=result.retrieval_budget,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {exc}",
        ) from exc