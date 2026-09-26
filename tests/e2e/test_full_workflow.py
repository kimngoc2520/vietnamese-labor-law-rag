from types import SimpleNamespace
from unittest.mock import patch

from src.generation.pipeline import GenerationPipeline


def test_full_generation_workflow():
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
            assert (
                query
                == "Người lao động có quyền đơn phương chấm dứt "
                "hợp đồng không?"
            )
            assert final_top_k == 5
            return fake_retrieval

    with (
        patch(
            "src.generation.pipeline.get_llm"
        ) as mock_get_llm,
        patch(
            "src.generation.pipeline.AdaptiveRetriever",
            FakeRetriever,
        ),
        patch(
            "src.generation.pipeline.SessionLocal",
            return_value=SimpleNamespace(close=lambda: None),
        ),
    ):
        mock_llm = mock_get_llm.return_value
        mock_llm.generate.return_value = fake_answer

        pipeline = GenerationPipeline()

        result = pipeline.run(
            query=(
                "Người lao động có quyền đơn phương "
                "chấm dứt hợp đồng không?"
            )
        )

    assert result.answer == fake_answer
    assert result.complexity == "Medium"
    assert result.retrieval_budget == 10
    assert isinstance(result.citations, list)
    assert isinstance(result.retrieved_chunks, list)
    assert len(result.retrieved_chunks) == 1