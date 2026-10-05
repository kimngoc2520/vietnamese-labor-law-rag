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

# ============================================================
# CONFIG
# ============================================================

DATASET_PATH = (
    ROOT_DIR
    / "evaluation"
    / "datasets"
    / "retrieval_eval.json"
)

GROUND_TRUTH_PATH = (
    ROOT_DIR
    / "evaluation"
    / "datasets"
    / "ground_truth_evidence.json"
)

RESULT_PATH = (
    ROOT_DIR
    / "evaluation"
    / "results"
    / "retrieval"
    / "hybrid_benchmark.json"
)


# ============================================================
# GROUND-TRUTH MATCHING
# ============================================================

def is_relevant(
    chunk: dict,
    ground_truth_source: dict,
) -> bool:
    """Check exact ground-truth chunk identity.

    A retrieved chunk is relevant only when both ``document_id`` and
    ``chunk_index`` match the annotated source exactly. This avoids
    article-level substring collisions such as ``Điều 3`` matching
    ``Điều 35``.
    """

    return (
        chunk.get("document_id")
        == ground_truth_source["document_id"]
        and chunk.get("chunk_index")
        == ground_truth_source["chunk_index"]
    )


def calculate_metrics(
    retrieved_chunks: list,
    ground_truth_source: dict,
    k_values: list,
):
    """Tính Hit Rate@K và MRR cho một ranking list."""

    hit_at_k = {
        k: 0.0
        for k in k_values
    }

    first_relevant_rank = None

    for rank, chunk in enumerate(
        retrieved_chunks,
        start=1,
    ):
        if is_relevant(
            chunk,
            ground_truth_source,
        ):
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


# ============================================================
# RESULT PERSISTENCE
# ============================================================

def save_results(
    *,
    num_queries: int,
    metrics: dict[str, dict[str, float]],
) -> None:
    """Save hybrid benchmark results as machine-readable JSON."""

    RESULT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = {
        "benchmark": "hybrid",
        "query_count": num_queries,
        "pipelines": metrics,
    }

    with RESULT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nSaved results to: {RESULT_PATH}"
    )


# ============================================================
# MAIN BENCHMARK
# ============================================================

def run_benchmark():
    print(
        "Benchmark: So sánh 4 Retrieval Strategies\n"
    )

    # ========================================================
    # Load evaluation dataset
    # ========================================================

    if not DATASET_PATH.exists():
        print(
            f"Không tìm thấy file: {DATASET_PATH}"
        )
        return

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        eval_data = json.load(file)

    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        ground_truth = json.load(file)

    gt_by_query = {
        item["query"].strip(): item["source"]
        for item in ground_truth
    }

    if len(gt_by_query) != len(ground_truth):
        raise ValueError(
            "ground_truth_evidence.json chứa query bị trùng."
        )

    missing_queries = [
        item["query"]
        for item in eval_data
        if item["query"].strip()
        not in gt_by_query
    ]

    if missing_queries:
        raise ValueError(
            "Không tìm thấy ground truth exact chunk cho "
            f"{len(missing_queries)} query trong "
            "retrieval_eval.json."
        )

    print(
        f"Loaded {len(eval_data)} queries\n"
    )

    db = SessionLocal()

    try:
        # ====================================================
        # Initialize Retrieval Components
        # ====================================================

        dense_retriever = DenseRetriever(db)

        bm25_retriever = BM25Retriever(db)

        hybrid_retriever = HybridRetriever()

        reranker = CrossEncoderReranker()

        k_values = [1, 3, 5]

        # ====================================================
        # Initialize Metrics
        # ====================================================

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

        # ====================================================
        # Run Evaluation
        # ====================================================

        for i, item in enumerate(
            eval_data,
            start=1,
        ):
            query = item["query"]

            ground_truth_source = gt_by_query[
                query.strip()
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

        # ====================================================
        # Calculate Average Metrics
        # ====================================================

        num_queries = len(eval_data)

        if num_queries == 0:
            print(
                "Evaluation dataset không có query."
            )
            return

        averaged_metrics = {}

        for pipeline_name, pipeline in pipelines.items():
            averaged_metrics[pipeline_name] = {
                f"Hit@{k}": (
                    pipeline["hit_rate"][k]
                    / num_queries
                )
                for k in k_values
            }

            averaged_metrics[pipeline_name]["MRR"] = (
                pipeline["mrr_sum"]
                / num_queries
            )

        # ====================================================
        # Save Machine-Readable Results
        # ====================================================

        save_results(
            num_queries=num_queries,
            metrics=averaged_metrics,
        )

        # ====================================================
        # Print Results
        # ====================================================

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

        # ----------------------------------------------------
        # Hit Rate@K
        # ----------------------------------------------------

        for k in k_values:
            row = (
                f"{'Hit@' + str(k):<15} | "
            )

            for pipeline_name in (
                "Dense",
                "Dense+Rerank",
                "Hybrid",
                "Hybrid+Rerank",
            ):
                score = averaged_metrics[
                    pipeline_name
                ][f"Hit@{k}"]

                row += (
                    f"{score:<12.4f} | "
                )

            print(row)

        # ----------------------------------------------------
        # MRR
        # ----------------------------------------------------

        mrr_row = (
            f"{'MRR':<15} | "
        )

        for pipeline_name in (
            "Dense",
            "Dense+Rerank",
            "Hybrid",
            "Hybrid+Rerank",
        ):
            mrr = averaged_metrics[
                pipeline_name
            ]["MRR"]

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