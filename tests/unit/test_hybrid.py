from src.retrieval.hybrid import HybridRetriever


def make_doc(
    document_id: str,
    chunk_index: int,
    content: str,
) -> dict:
    return {
        "document_id": document_id,
        "chunk_index": chunk_index,
        "content": content,
    }


def test_fuse_combines_multiple_ranking_lists() -> None:
    retriever = HybridRetriever()

    dense_results = [
        make_doc("doc1", 0, "Dense result 1"),
        make_doc("doc2", 0, "Dense result 2"),
    ]

    bm25_results = [
        make_doc("doc2", 0, "BM25 result 2"),
        make_doc("doc3", 0, "BM25 result 3"),
    ]

    results = retriever.fuse(
        [dense_results, bm25_results],
        top_k=10,
    )

    assert len(results) == 3
    assert {
        (result["document_id"], result["chunk_index"])
        for result in results
    } == {
        ("doc1", 0),
        ("doc2", 0),
        ("doc3", 0),
    }


def test_rrf_score_is_accumulated_for_documents_in_multiple_sources() -> None:
    retriever = HybridRetriever()

    dense_results = [
        make_doc("doc1", 0, "Dense result"),
    ]

    bm25_results = [
        make_doc("doc1", 0, "BM25 result"),
    ]

    results = retriever.fuse(
        [dense_results, bm25_results],
        top_k=10,
    )

    assert len(results) == 1

    expected_score = (
        1 / (retriever.RRF_K + 1)
        + 1 / (retriever.RRF_K + 1)
    )

    assert results[0]["rrf_score"] == expected_score


def test_retrieval_sources_are_recorded() -> None:
    retriever = HybridRetriever()

    dense_results = [
        make_doc("doc1", 0, "Dense result"),
    ]

    bm25_results = [
        make_doc("doc1", 0, "BM25 result"),
    ]

    results = retriever.fuse(
        [dense_results, bm25_results],
    )

    assert results[0]["retrieval_sources"] == [
        "dense",
        "bm25",
    ]


def test_document_only_in_one_source_keeps_single_source() -> None:
    retriever = HybridRetriever()

    dense_results = [
        make_doc("dense_only", 0, "Dense result"),
    ]

    bm25_results = [
        make_doc("bm25_only", 0, "BM25 result"),
    ]

    results = retriever.fuse(
        [dense_results, bm25_results],
    )

    sources = {
        result["document_id"]: result["retrieval_sources"]
        for result in results
    }

    assert sources["dense_only"] == ["dense"]
    assert sources["bm25_only"] == ["bm25"]


def test_results_are_sorted_by_rrf_score() -> None:
    retriever = HybridRetriever()

    dense_results = [
        make_doc("doc1", 0, "Doc 1"),
        make_doc("doc2", 0, "Doc 2"),
    ]

    bm25_results = [
        make_doc("doc1", 0, "Doc 1"),
        make_doc("doc3", 0, "Doc 3"),
    ]

    results = retriever.fuse(
        [dense_results, bm25_results],
    )

    assert results[0]["document_id"] == "doc1"
    assert (
        results[0]["rrf_score"]
        > results[1]["rrf_score"]
    )


def test_top_k_limits_number_of_results() -> None:
    retriever = HybridRetriever()

    dense_results = [
        make_doc("doc1", 0, "Doc 1"),
        make_doc("doc2", 0, "Doc 2"),
        make_doc("doc3", 0, "Doc 3"),
    ]

    results = retriever.fuse(
        [dense_results],
        top_k=2,
    )

    assert len(results) == 2
    assert [
        result["document_id"]
        for result in results
    ] == ["doc1", "doc2"]


def test_document_identity_uses_document_id_and_chunk_index() -> None:
    retriever = HybridRetriever()

    dense_results = [
        make_doc("doc1", 0, "Chunk 0"),
        make_doc("doc1", 1, "Chunk 1"),
    ]

    results = retriever.fuse(
        [dense_results],
        top_k=10,
    )

    assert len(results) == 2
    assert [
        (result["document_id"], result["chunk_index"])
        for result in results
    ] == [
        ("doc1", 0),
        ("doc1", 1),
    ]


def test_additional_ranking_list_gets_generic_source_name() -> None:
    retriever = HybridRetriever()

    ranking_lists = [
        [make_doc("doc1", 0, "Dense")],
        [make_doc("doc2", 0, "BM25")],
        [make_doc("doc3", 0, "Third retriever")],
    ]

    results = retriever.fuse(
        ranking_lists,
        top_k=10,
    )

    sources = {
        result["document_id"]: result["retrieval_sources"]
        for result in results
    }

    assert sources["doc3"] == ["retriever_2"]


def test_empty_ranking_lists_return_empty_results() -> None:
    retriever = HybridRetriever()

    assert retriever.fuse([], top_k=10) == []
    assert retriever.fuse([[], []], top_k=10) == []