from types import SimpleNamespace

import pytest

from src.generation.pipeline import GenerationPipeline


def make_pipeline(monkeypatch):
    pipeline = object.__new__(GenerationPipeline)

    pipeline.llm = SimpleNamespace(
        generate=lambda **kwargs: "Mock answer"
    )

    return pipeline


def make_retrieval_result(
    results=None,
    complexity="Medium",
    budget=10,
):
    if results is None:
        results = [
            {
                "chunk_id": "chunk-1",
                "content": "Điều 35 quy định về quyền đơn phương chấm dứt hợp đồng.",
                "article_title": "Điều 35",
                "rerank_score": 0.9,
            }
        ]

    return SimpleNamespace(
        results=results,
        complexity=SimpleNamespace(level=complexity),
        budget=SimpleNamespace(top_k=budget),
    )


def test_generation_pipeline_runs_full_workflow(monkeypatch):
    pipeline = make_pipeline(monkeypatch)

    retrieval = make_retrieval_result()

    class FakeRetriever:
        def __init__(self, db):
            pass

        def retrieve(self, query, final_top_k):
            assert query == "Người lao động có quyền gì?"
            assert final_top_k == 5
            return retrieval

    monkeypatch.setattr(
        "src.generation.pipeline.AdaptiveRetriever",
        FakeRetriever,
    )

    monkeypatch.setattr(
        "src.generation.pipeline.SessionLocal",
        lambda: SimpleNamespace(
            close=lambda: None
        ),
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_prompt",
        lambda query, context: "MOCK PROMPT",
    )

    monkeypatch.setattr(
        "src.generation.pipeline.select_evidence",
        lambda answer, evidence: evidence,
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_citations",
        lambda evidence: ["Điều 35"],
    )

    result = pipeline.run(
        "Người lao động có quyền gì?"
    )

    assert result.answer == "Mock answer"
    assert result.citations == ["Điều 35"]
    assert result.retrieved_chunks == retrieval.results
    assert result.complexity == "Medium"
    assert result.retrieval_budget == 10


def test_generation_pipeline_builds_context_from_retrieved_chunks(
    monkeypatch,
):
    pipeline = make_pipeline(monkeypatch)

    retrieval = make_retrieval_result(
        results=[
            {
                "chunk_id": "chunk-1",
                "content": "Nội dung thứ nhất",
            },
            {
                "chunk_id": "chunk-2",
                "content": "",
            },
            {
                "chunk_id": "chunk-3",
                "content": "Nội dung thứ ba",
            },
        ]
    )

    captured = {}

    class FakeRetriever:
        def __init__(self, db):
            pass

        def retrieve(self, query, final_top_k):
            return retrieval

    def fake_build_prompt(query, context):
        captured["context"] = context
        return "MOCK PROMPT"

    monkeypatch.setattr(
        "src.generation.pipeline.AdaptiveRetriever",
        FakeRetriever,
    )

    monkeypatch.setattr(
        "src.generation.pipeline.SessionLocal",
        lambda: SimpleNamespace(close=lambda: None),
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_prompt",
        fake_build_prompt,
    )

    monkeypatch.setattr(
        "src.generation.pipeline.select_evidence",
        lambda answer, evidence: [],
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_citations",
        lambda evidence: [],
    )

    pipeline.run("test query")

    assert captured["context"] == [
        "Nội dung thứ nhất",
        "Nội dung thứ ba",
    ]


def test_generation_pipeline_passes_context_to_llm(
    monkeypatch,
):
    pipeline = make_pipeline(monkeypatch)

    retrieval = make_retrieval_result()

    captured = {}

    class FakeRetriever:
        def __init__(self, db):
            pass

        def retrieve(self, query, final_top_k):
            return retrieval

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return "Generated answer"

    pipeline.llm.generate = fake_generate

    monkeypatch.setattr(
        "src.generation.pipeline.AdaptiveRetriever",
        FakeRetriever,
    )

    monkeypatch.setattr(
        "src.generation.pipeline.SessionLocal",
        lambda: SimpleNamespace(close=lambda: None),
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_prompt",
        lambda query, context: "MOCK PROMPT",
    )

    monkeypatch.setattr(
        "src.generation.pipeline.select_evidence",
        lambda answer, evidence: [],
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_citations",
        lambda evidence: [],
    )

    pipeline.run("test query")

    assert captured["prompt"] == "MOCK PROMPT"
    assert captured["query"] == "test query"
    assert captured["context"] == (
        "Điều 35 quy định về quyền đơn phương chấm dứt hợp đồng."
    )


def test_generation_pipeline_selects_evidence_and_builds_citations(
    monkeypatch,
):
    pipeline = make_pipeline(monkeypatch)

    retrieval = make_retrieval_result()

    captured = {}

    class FakeRetriever:
        def __init__(self, db):
            pass

        def retrieve(self, query, final_top_k):
            return retrieval

    def fake_select_evidence(answer, evidence):
        captured["answer"] = answer
        captured["evidence"] = evidence
        return ["selected-evidence"]

    def fake_build_citations(evidence):
        captured["selected"] = evidence
        return ["Điều 35"]

    monkeypatch.setattr(
        "src.generation.pipeline.AdaptiveRetriever",
        FakeRetriever,
    )

    monkeypatch.setattr(
        "src.generation.pipeline.SessionLocal",
        lambda: SimpleNamespace(close=lambda: None),
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_prompt",
        lambda query, context: "PROMPT",
    )

    pipeline.llm.generate = lambda **kwargs: "Generated answer"

    monkeypatch.setattr(
        "src.generation.pipeline.select_evidence",
        fake_select_evidence,
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_citations",
        fake_build_citations,
    )

    result = pipeline.run("test query")

    assert captured["answer"] == "Generated answer"
    assert captured["evidence"] == retrieval.results
    assert captured["selected"] == ["selected-evidence"]
    assert result.citations == ["Điều 35"]


def test_generation_pipeline_closes_database_session(
    monkeypatch,
):
    pipeline = make_pipeline(monkeypatch)

    retrieval = make_retrieval_result()

    closed = {"value": False}

    class FakeDB:
        def close(self):
            closed["value"] = True

    class FakeRetriever:
        def __init__(self, db):
            pass

        def retrieve(self, query, final_top_k):
            return retrieval

    monkeypatch.setattr(
        "src.generation.pipeline.SessionLocal",
        lambda: FakeDB(),
    )

    monkeypatch.setattr(
        "src.generation.pipeline.AdaptiveRetriever",
        FakeRetriever,
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_prompt",
        lambda query, context: "PROMPT",
    )

    monkeypatch.setattr(
        "src.generation.pipeline.select_evidence",
        lambda answer, evidence: [],
    )

    monkeypatch.setattr(
        "src.generation.pipeline.build_citations",
        lambda evidence: [],
    )

    pipeline.run("test query")

    assert closed["value"] is True