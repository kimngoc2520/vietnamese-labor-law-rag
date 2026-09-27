from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.observability.latency import reset_latency
from src.observability.metrics import reset_metrics


def test_metrics_reflect_generation_request() -> None:
    reset_latency()
    reset_metrics()

    fake_answer = (
        "Theo Khoản 1 Điều 35, người lao động có quyền "
        "đơn phương chấm dứt hợp đồng lao động."
    )

    fake_retrieval = SimpleNamespace(
        results=[
            {
                "chunk_id": "chunk-1",
                "content": (
                    "Điều 35. Quyền đơn phương chấm dứt hợp đồng "
                    "lao động của người lao động."
                ),
                "article_title": "Điều 35",
                "rerank_score": 0.95,
            }
        ],
        complexity=SimpleNamespace(level="Medium"),
        budget=SimpleNamespace(top_k=10),
    )

    class FakeRetriever:
        def __init__(self, db):
            pass

        def retrieve(self, query, final_top_k):
            return fake_retrieval

    with (
        patch("src.generation.pipeline.get_llm") as mock_get_llm,
        patch("src.generation.pipeline.AdaptiveRetriever", FakeRetriever),
        patch(
            "src.generation.pipeline.SessionLocal",
            return_value=SimpleNamespace(close=lambda: None),
        ),
    ):
        mock_llm = mock_get_llm.return_value
        mock_llm.generate.return_value = fake_answer

        client = TestClient(app)

        response = client.post(
            "/chat",
            json={
                "query": (
                    "Người lao động có quyền đơn phương "
                    "chấm dứt hợp đồng không?"
                )
            },
        )

        assert response.status_code == 200

        metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200

    data = metrics_response.json()

    assert data["metrics"]["total_requests"]["count"] == 1
    assert data["metrics"]["successful_requests"]["count"] == 1

    assert "retrieval" in data["latency"]
    assert "generation" in data["latency"]
    assert "total" in data["latency"]

    assert data["latency"]["retrieval"]["count"] == 1
    assert data["latency"]["generation"]["count"] == 1
    assert data["latency"]["total"]["count"] == 1