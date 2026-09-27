from fastapi import APIRouter

from src.observability.latency import get_latency_summary
from src.observability.metrics import get_metric_summary

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> dict[str, dict[str, dict[str, float | int]]]:
    return {
        "latency": get_latency_summary(),
        "metrics": get_metric_summary(),
    }