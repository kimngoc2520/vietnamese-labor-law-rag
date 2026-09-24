from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ingestion.pipeline import IngestionPipeline


def make_pipeline():
    pipeline = object.__new__(IngestionPipeline)

    pipeline.loader = SimpleNamespace()
    pipeline.cleaner = SimpleNamespace()
    pipeline.chunker = SimpleNamespace()
    pipeline.embedder = SimpleNamespace()
    pipeline.indexer = SimpleNamespace()

    return pipeline


def test_process_file_runs_full_ingestion_pipeline():
    pipeline = make_pipeline()

    file_path = Path("sample.pdf")

    pipeline.loader.load = lambda path: (
        "raw document text",
        {"document_id": "DOC-001"},
    )

    pipeline.cleaner.clean = lambda text: (
        text.strip()
    )

    chunks = [
        SimpleNamespace(content="chunk 1"),
        SimpleNamespace(content="chunk 2"),
    ]

    pipeline.chunker.split = lambda text, metadata: chunks

    embeddings = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    pipeline.embedder.embed = lambda texts: embeddings

    indexed = {
        "document": None,
        "chunks": None,
        "embeddings": None,
    }

    pipeline.indexer.upsert_document = (
        lambda metadata: indexed.update(
            document=metadata
        )
    )

    pipeline.indexer.upsert_chunks = (
        lambda chunks_arg, embeddings_arg: indexed.update(
            chunks=chunks_arg,
            embeddings=embeddings_arg,
        )
    )

    result = pipeline.process_file(file_path)

    assert result == 2

    assert indexed["document"]["document_id"] == "DOC-001"
    assert indexed["chunks"] == chunks
    assert indexed["embeddings"] == embeddings


def test_process_file_merges_fallback_and_file_metadata():
    pipeline = make_pipeline()

    pipeline.loader.load = lambda path: (
        "raw text",
        {
            "document_id": "DOC-001",
            "title": "Loaded title",
        },
    )

    pipeline.cleaner.clean = lambda text: text

    chunks = [
        SimpleNamespace(content="chunk"),
    ]

    pipeline.chunker.split = (
        lambda text, metadata: chunks
    )

    pipeline.embedder.embed = lambda texts: [
        [0.1, 0.2]
    ]

    captured_metadata = {}

    pipeline.indexer.upsert_document = (
        lambda metadata: captured_metadata.update(
            metadata
        )
    )

    pipeline.indexer.upsert_chunks = (
        lambda chunks, embeddings: None
    )

    result = pipeline.process_file(
        Path("sample.pdf"),
        fallback_metadata={
            "document_id": "FALLBACK-001",
            "source": "fallback",
        },
    )

    assert result == 1
    assert captured_metadata["document_id"] == "DOC-001"
    assert captured_metadata["source"] == "fallback"
    assert captured_metadata["title"] == "Loaded title"


def test_process_file_requires_document_id():
    pipeline = make_pipeline()

    pipeline.loader.load = lambda path: (
        "raw text",
        {},
    )

    with pytest.raises(
        ValueError,
        match="Thiếu document_id",
    ):
        pipeline.process_file(Path("sample.pdf"))


def test_process_file_rejects_empty_clean_text():
    pipeline = make_pipeline()

    pipeline.loader.load = lambda path: (
        "raw text",
        {"document_id": "DOC-001"},
    )

    pipeline.cleaner.clean = lambda text: ""

    with pytest.raises(
        ValueError,
        match="Không trích xuất được nội dung",
    ):
        pipeline.process_file(Path("sample.pdf"))


def test_process_file_returns_zero_when_no_chunks():
    pipeline = make_pipeline()

    pipeline.loader.load = lambda path: (
        "raw text",
        {"document_id": "DOC-001"},
    )

    pipeline.cleaner.clean = lambda text: text

    pipeline.chunker.split = (
        lambda text, metadata: []
    )

    pipeline.embedder.embed = lambda texts: []

    result = pipeline.process_file(
        Path("sample.pdf")
    )

    assert result == 0


def test_process_file_rejects_embedding_count_mismatch():
    pipeline = make_pipeline()

    pipeline.loader.load = lambda path: (
        "raw text",
        {"document_id": "DOC-001"},
    )

    pipeline.cleaner.clean = lambda text: text

    chunks = [
        SimpleNamespace(content="chunk 1"),
        SimpleNamespace(content="chunk 2"),
    ]

    pipeline.chunker.split = (
        lambda text, metadata: chunks
    )

    pipeline.embedder.embed = lambda texts: [
        [0.1, 0.2]
    ]

    with pytest.raises(
        ValueError,
        match="Số lượng embeddings không khớp",
    ):
        pipeline.process_file(
            Path("sample.pdf")
        )