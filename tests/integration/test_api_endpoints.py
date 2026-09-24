from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200


def test_chat_endpoint():
    with patch(
        "src.api.routes.chat.GenerationPipeline"
    ) as mock_pipeline:
        mock_result = mock_pipeline.return_value.run.return_value

        mock_result.answer = "Test answer."
        mock_result.citations = ["Điều 35"]
        mock_result.complexity = "Medium"
        mock_result.retrieval_budget = 10

        response = client.post(
            "/chat",
            json={
                "query": "Test labor law question"
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "Test labor law question"
    assert data["answer"] == "Test answer."
    assert data["citations"] == ["Điều 35"]
    assert data["complexity"] == "Medium"
    assert data["retrieval_budget"] == 10


def test_chat_rejects_empty_query():
    response = client.post(
        "/chat",
        json={"query": ""},
    )

    assert response.status_code == 422


def test_feedback_endpoint():
    response = client.post(
        "/feedback",
        json={
            "query": "Test question",
            "rating": "positive",
            "comment": "Helpful answer.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "accepted"


def test_feedback_rejects_invalid_rating():
    response = client.post(
        "/feedback",
        json={
            "query": "Test question",
            "rating": "invalid",
        },
    )

    assert response.status_code == 422