# ruff: noqa: E402
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.db.connection import SessionLocal
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.sparse import BM25Retriever


def is_relevant(
    chunk: dict,
    ground_truth_source: dict,
) -> bool:
    """Check exact ground-truth chunk identity.

    A retrieved chunk is relevant only when both ``document_id`` and
    ``chunk_index`` match the annotated source exactly.  This avoids
    article-level substring collisions such as ``Điều 3`` matching
    ``Điều 35``.
    """

    return (
        chunk.get("document_id") == ground_truth_source["document_id"]
        and chunk.get("chunk_index") == ground_truth_source["chunk_index"]
    )


def calculate_metrics(
    retrieved_chunks: list,
    ground_truth_source: dict,
    k_values: list,
):
    """
    Tính Hit Rate@K và MRR cho một ranking list.
    """

    hit_at_k = {
        k: 0.0
        for k in k_values
    }

    first_relevant_rank = None

    for rank, chunk in enumerate(
        retrieved_chunks,
        start=1,
    ):
        if is_relevant(chunk, ground_truth_source):
            if first_relevant_rank is None:
                first_relevant_rank = rank

            for k in k_values:
                if rank <= k:
                    hit_at_k[k] = 1.0

    mrr = (
        1.0 / first_relevant_rank
        if first_relevant_rank is not None
        else 0.0
    )

    return hit_at_k, mrr


def run_benchmark():
    print(
        "Benchmark: So sánh 4 Retrieval Strategies\n"
    )

    dataset_path = Path(
        "evaluation/datasets/retrieval_eval.json"
    )

    if not dataset_path.exists():
        print(
            f"Không tìm thấy file: {dataset_path}"
        )
        return

    with dataset_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        eval_data = json.load(file)

    ground_truth_path = Path(
        "evaluation/datasets/ground_truth_evidence.json"
    )

    with ground_truth_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        ground_truth = json.load(file)

    gt_by_query = {item["query"].strip(): item["source"] for item in ground_truth}

    if len(gt_by_query) != len(ground_truth):
        raise ValueError("ground_truth_evidence.json chứa query bị trùng.")

    missing_queries = [
        item["query"]
        for item in eval_data
        if item["query"].strip() not in gt_by_query
    ]
    if missing_queries:
        raise ValueError(
            "Không tìm thấy ground truth exact chunk cho "
            f"{len(missing_queries)} query trong retrieval_eval.json."
        )

    print(
        f"Loaded {len(eval_data)} queries\n"
    )

    db = SessionLocal()

    try:
        # ==================================================
        # Initialize Retrieval Components
        # ==================================================

        dense_retriever = DenseRetriever(db)

        bm25_retriever = BM25Retriever(db)

        hybrid_retriever = HybridRetriever()

        reranker = CrossEncoderReranker()

        k_values = [1, 3, 5]

        # ==================================================
        # Initialize Metrics
        # ==================================================

        pipelines = {
            "Dense": {
                "hit_rate": {
                    k: 0.0
                    for k in k_values
                },
                "mrr_sum": 0.0,
            },
            "Dense+Rerank": {
                "hit_rate": {
                    k: 0.0
                    for k in k_values
                },
                "mrr_sum": 0.0,
            },
            "Hybrid": {
                "hit_rate": {
                    k: 0.0
                    for k in k_values
                },
                "mrr_sum": 0.0,
            },
            "Hybrid+Rerank": {
                "hit_rate": {
                    k: 0.0
                    for k in k_values
                },
                "mrr_sum": 0.0,
            },
        }

        # ==================================================
        # Run Evaluation
        # ==================================================

        for i, item in enumerate(
            eval_data,
            start=1,
        ):
            query = item["query"]

            relevant_doc_ids = item[
                "relevant_document_ids"
            ]

            relevant_articles = item[
                "relevant_articles"
            ]

            print(
                f"[{i}/{len(eval_data)}] "
                f"'{query[:50]}...'"
            )

            # ==================================================
            # 1. Dense Retrieval
            # ==================================================

            dense_results = (
                dense_retriever.retrieve(
                    query,
                    top_k=10,
                )
            )

            hits, mrr = calculate_metrics(
                dense_results,
                ground_truth_source,
                k_values,
            )

            for k in k_values:
                pipelines["Dense"]["hit_rate"][k] += (
                    hits[k]
                )

            pipelines["Dense"]["mrr_sum"] += mrr

            # ==================================================
            # 2. Dense + Reranker
            # ==================================================

            reranked_results = (
                reranker.rerank(
                    query,
                    dense_results,
                    top_k=5,
                )
            )

            hits, mrr = calculate_metrics(
                reranked_results,
                ground_truth_source,
                k_values,
            )

            for k in k_values:
                pipelines[
                    "Dense+Rerank"
                ]["hit_rate"][k] += hits[k]

            pipelines[
                "Dense+Rerank"
            ]["mrr_sum"] += mrr

            # ==================================================
            # 3. Hybrid Retrieval
            #
            # Dense + BM25 + RRF
            # ==================================================

            bm25_results = (
                bm25_retriever.retrieve(
                    query,
                    top_k=10,
                )
            )

            hybrid_results = (
                hybrid_retriever.fuse(
                    ranking_lists=[
                        dense_results,
                        bm25_results,
                    ],
                    top_k=10,
                )
            )

            hits, mrr = calculate_metrics(
                hybrid_results,
                ground_truth_source,
                k_values,
            )

            for k in k_values:
                pipelines["Hybrid"]["hit_rate"][k] += (
                    hits[k]
                )

            pipelines["Hybrid"]["mrr_sum"] += mrr

            # ==================================================
            # 4. Hybrid + Reranker
            # ==================================================

            hybrid_reranked_results = (
                reranker.rerank(
                    query,
                    hybrid_results,
                    top_k=5,
                )
            )

            hits, mrr = calculate_metrics(
                hybrid_reranked_results,
                ground_truth_source,
                k_values,
            )

            for k in k_values:
                pipelines[
                    "Hybrid+Rerank"
                ]["hit_rate"][k] += hits[k]

            pipelines[
                "Hybrid+Rerank"
            ]["mrr_sum"] += mrr

        # ==================================================
        # Calculate Average Metrics
        # ==================================================

        num_queries = len(eval_data)

        if num_queries == 0:
            print(
                "Evaluation dataset không có query."
            )
            return

        # ==================================================
        # Print Results
        # ==================================================

        print("\n" + "=" * 90)

        print(
            "KẾT QUẢ ABLATION STUDY: "
            "4 RETRIEVAL STRATEGIES"
        )

        print("=" * 90)

        print(
            f"{'Metric':<15} | "
            f"{'Dense':<12} | "
            f"{'Dense+Rerank':<14} | "
            f"{'Hybrid':<12} | "
            f"{'Hybrid+Rerank':<14}"
        )

        print("-" * 90)

        # --------------------------------------------------
        # Hit Rate@K
        # --------------------------------------------------

        for k in k_values:
            row = (
                f"{'Hit@' + str(k):<15} | "
            )

            for pipeline in pipelines.values():
                score = (
                    pipeline["hit_rate"][k]
                    / num_queries
                )

                row += (
                    f"{score:<12.4f} | "
                )

            print(row)

        # --------------------------------------------------
        # MRR
        # --------------------------------------------------

        mrr_row = (
            f"{'MRR':<15} | "
        )

        for pipeline in pipelines.values():
            mrr = (
                pipeline["mrr_sum"]
                / num_queries
            )

            mrr_row += (
                f"{mrr:<12.4f} | "
            )

        print(mrr_row)

        print("=" * 90)

        print(
            "\nBenchmark hoàn tất!"
        )

        print(
            "Kết quả dùng để so sánh Dense, "
            "Dense+Reranker, Hybrid và "
            "Hybrid+Reranker."
        )

    finally:
        db.close()


if __name__ == "__main__":
    run_benchmark()