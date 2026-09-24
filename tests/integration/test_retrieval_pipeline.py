from types import SimpleNamespace

import pytest

from src.retrieval.adaptive import AdaptiveRetriever


def make_retriever(monkeypatch):
    """
    Tạo AdaptiveRetriever mà không tải model/database thật.
    """

    monkeypatch.setattr(
        "src.retrieval.adaptive.DenseRetriever",
        lambda db_session: SimpleNamespace(),
    )

    monkeypatch.setattr(
        "src.retrieval.adaptive.BM25Retriever",
        lambda db_session: SimpleNamespace(),
    )

    monkeypatch.setattr(
        "src.retrieval.adaptive.CrossEncoderReranker",
        lambda: SimpleNamespace(),
    )

    retriever = AdaptiveRetriever(db_session=None)

    return retriever


def test_retrieval_pipeline_uses_adaptive_budget(monkeypatch):
    retriever = make_retriever(monkeypatch)

    retriever.classifier = SimpleNamespace(
        classify=lambda query: SimpleNamespace(
            level="Complex",
            confidence=0.95,
        )
    )

    dense_calls = []
    bm25_calls = []
    hybrid_calls = []
    reranker_calls = []

    retriever.dense.retrieve = lambda query, top_k: (
        dense_calls.append((query, top_k))
        or [
            {
                "chunk_id": "dense-1",
                "content": "Dense result",
            }
        ]
    )

    retriever.bm25.retrieve = lambda query, top_k: (
        bm25_calls.append((query, top_k))
        or [
            {
                "chunk_id": "bm25-1",
                "content": "BM25 result",
            }
        ]
    )

    retriever.hybrid.fuse = lambda result_lists, top_k: (
        hybrid_calls.append((result_lists, top_k))
        or [
            {
                "chunk_id": "hybrid-1",
                "content": "Hybrid result",
                "article_title": "Điều 35",
            }
        ]
    )

    retriever.reranker.rerank = (
        lambda query, candidates, top_k: (
            reranker_calls.append(
                (query, candidates, top_k)
            )
            or [
                {
                    "chunk_id": "hybrid-1",
                    "content": "Hybrid result",
                    "article_title": "Điều 35",
                    "rerank_score": 0.9,
                }
            ]
        )
    )

    result = retriever.retrieve(
        "Câu hỏi phức tạp về luật lao động",
        final_top_k=5,
    )

    assert result.budget.complexity == "Complex"
    assert result.budget.top_k == 20

    assert dense_calls == [
        ("Câu hỏi phức tạp về luật lao động", 20)
    ]

    assert bm25_calls == [
        ("Câu hỏi phức tạp về luật lao động", 20)
    ]

    assert hybrid_calls[0][1] == 20
    assert reranker_calls[0][2] == 1

    assert len(result.candidates) == 1
    assert len(result.results) == 1


@pytest.mark.parametrize(
    ("complexity", "expected_top_k"),
    [
        ("Simple", 5),
        ("Medium", 10),
        ("Complex", 20),
    ],
)
def test_retrieval_pipeline_maps_complexity_to_top_k(
    monkeypatch,
    complexity,
    expected_top_k,
):
    retriever = make_retriever(monkeypatch)

    assert retriever.get_top_k(complexity) == expected_top_k


def test_retrieval_pipeline_rejects_empty_query(monkeypatch):
    retriever = make_retriever(monkeypatch)

    with pytest.raises(ValueError, match="Query không được để trống"):
        retriever.retrieve("")


def test_retrieval_pipeline_rejects_invalid_final_top_k(
    monkeypatch,
):
    retriever = make_retriever(monkeypatch)

    with pytest.raises(
        ValueError,
        match="final_top_k phải lớn hơn 0",
    ):
        retriever.retrieve(
            "Câu hỏi về luật lao động",
            final_top_k=0,
        )