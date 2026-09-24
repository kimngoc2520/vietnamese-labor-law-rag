from unittest.mock import patch

from src.generation.pipeline import GenerationPipeline


def test_full_generation_workflow():
    fake_answer = (
        "Theo Khoản 1 Điều 35, người lao động có quyền "
        "đơn phương chấm dứt hợp đồng lao động."
    )

    with patch(
        "src.generation.pipeline.get_llm"
    ) as mock_get_llm:
        mock_llm = mock_get_llm.return_value
        mock_llm.generate.return_value = fake_answer

        pipeline = GenerationPipeline()

        result = pipeline.run(
            query="Người lao động có quyền đơn phương chấm dứt hợp đồng không?"
        )

    assert result.answer == fake_answer
    assert result.complexity in {
        "Simple",
        "Medium",
        "Complex",
    }

    assert result.retrieval_budget > 0
    assert isinstance(result.citations, list)
    assert isinstance(result.retrieved_chunks, list)