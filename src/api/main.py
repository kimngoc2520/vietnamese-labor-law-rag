from fastapi import FastAPI

from src.api.routes.chat import router as chat_router
from src.api.routes.feedback import router as feedback_router
from src.api.routes.health import router as health_router
from src.api.routes.ingest import router as ingest_router


app = FastAPI(
    title="Vietnamese Labor Law RAG",
    description="Adaptive RAG Agent for Vietnamese labor law.",
    version="0.1.0",
)


app.include_router(health_router)
app.include_router(chat_router)
app.include_router(feedback_router)
app.include_router(ingest_router)