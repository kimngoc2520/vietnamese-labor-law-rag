from src.retrieval.reranker import rerank


def test_rerank_preserves_documents() -> None:
    documents = [{"content": "context"}]
    assert rerank("query", documents) == documents
