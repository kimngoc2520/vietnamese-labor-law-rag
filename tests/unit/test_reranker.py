from src.retrieval.reranker import CrossEncoderReranker


def test_rerank_returns_empty_for_no_candidates() -> None:
    reranker = object.__new__(CrossEncoderReranker)

    assert reranker.rerank("query", []) == []


def test_rerank_assigns_scores_and_sorts() -> None:
    reranker = object.__new__(CrossEncoderReranker)

    class FakeModel:
        def predict(self, pairs, show_progress_bar=False):
            assert pairs == [
                ("query", "document A"),
                ("query", "document B"),
                ("query", "document C"),
            ]
            return [0.2, 0.9, 0.5]

    reranker.model = FakeModel()

    documents = [
        {"content": "document A"},
        {"content": "document B"},
        {"content": "document C"},
    ]

    result = reranker.rerank("query", documents, top_k=3)

    assert [doc["content"] for doc in result] == [
        "document B",
        "document C",
        "document A",
    ]

    assert [doc["rerank_score"] for doc in result] == [
        0.9,
        0.5,
        0.2,
    ]


def test_rerank_respects_top_k() -> None:
    reranker = object.__new__(CrossEncoderReranker)

    class FakeModel:
        def predict(self, pairs, show_progress_bar=False):
            return [0.2, 0.9, 0.5]

    reranker.model = FakeModel()

    documents = [
        {"content": "document A"},
        {"content": "document B"},
        {"content": "document C"},
    ]

    result = reranker.rerank("query", documents, top_k=2)

    assert len(result) == 2
    assert [doc["content"] for doc in result] == [
        "document B",
        "document C",
    ]