import json
from io import BytesIO
from typing import Self
from urllib.error import HTTPError, URLError

from app import ChatClientError, ask_chat, get_api_base_url


class FakeResponse:
    def __init__(self, body: str, status: int = 200) -> None:
        self._body = body.encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_get_api_base_url_defaults_to_localhost(monkeypatch) -> None:
    monkeypatch.delenv("API_BASE_URL", raising=False)
    assert get_api_base_url() == "http://localhost:8000"


def test_get_api_base_url_uses_environment(monkeypatch) -> None:
    monkeypatch.setenv("API_BASE_URL", "http://api:8000/")
    assert get_api_base_url() == "http://api:8000"


def test_ask_chat_rejects_empty_query() -> None:
    try:
        ask_chat("   ")
    except ChatClientError as exc:
        assert "enter a question" in str(exc)
    else:
        raise AssertionError("Expected ChatClientError")


def test_ask_chat_returns_parsed_payload(monkeypatch) -> None:
    payload = {
        "query": "test",
        "answer": "Theo Điều 35...",
        "citations": ["Điều 35, Bộ luật Lao động 2019"],
        "complexity": "Medium",
        "retrieval_budget": 10,
    }

    def fake_urlopen(request, timeout):
        assert request.full_url == "http://localhost:8000/chat"
        assert timeout == 180
        return FakeResponse(json.dumps(payload))

    monkeypatch.setattr("app.urlopen", fake_urlopen)
    result = ask_chat("test")

    assert result["answer"] == payload["answer"]
    assert result["citations"] == payload["citations"]
    assert result["retrieval_budget"] == 10


def test_ask_chat_handles_unavailable_backend(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise URLError("connection refused")

    monkeypatch.setattr("app.urlopen", fake_urlopen)

    try:
        ask_chat("Câu hỏi thử")
    except ChatClientError as exc:
        assert "unavailable" in str(exc).lower()
    else:
        raise AssertionError("Expected ChatClientError")


def test_ask_chat_handles_http_error(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise HTTPError(
            url="http://localhost:8000/chat",
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=BytesIO(
                json.dumps({"detail": "Generation failed"}).encode("utf-8")
            ),
        )

    monkeypatch.setattr("app.urlopen", fake_urlopen)

    try:
        ask_chat("Câu hỏi thử")
    except ChatClientError as exc:
        assert "HTTP 500" in str(exc)
        assert "Generation failed" in str(exc)
    else:
        raise AssertionError("Expected ChatClientError")


def test_ask_chat_rejects_invalid_json(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse("not-json")

    monkeypatch.setattr("app.urlopen", fake_urlopen)

    try:
        ask_chat("Câu hỏi thử")
    except ChatClientError as exc:
        assert "not valid JSON" in str(exc)
    else:
        raise AssertionError("Expected ChatClientError")


def test_ask_chat_rejects_missing_fields(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse(json.dumps({"query": "x", "answer": "y"}))

    monkeypatch.setattr("app.urlopen", fake_urlopen)

    try:
        ask_chat("Câu hỏi thử")
    except ChatClientError as exc:
        assert "missing required fields" in str(exc)
    else:
        raise AssertionError("Expected ChatClientError")