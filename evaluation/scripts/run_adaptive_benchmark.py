import json
import sys
from pathlib import Path
from typing import Any

# evaluation/scripts/run_adaptive_benchmark.py
# Repo root = parents[2]
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2]),
)

from src.db.connection import SessionLocal
from src.retrieval.adaptive import AdaptiveRetriever
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.sparse import BM25Retriever

# ============================================================
# CONFIG
# ============================================================

DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "ground_truth_evidence.json"
)

FIXED_K_VALUES = [5, 10, 20]
FINAL_TOP_K = 5


# ============================================================
# DATASET
# ============================================================

def load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# GROUND-TRUTH MATCHING
# ============================================================

def is_relevant(
    result: dict[str, Any],
    item: dict[str, Any],
) -> bool:
    """
    A result is relevant only when both document_id
    and chunk_index exactly match the ground-truth evidence.
    """

    expected_source = item["source"]

    return (
        result["document_id"] == expected_source["document_id"]
        and result["chunk_index"] == expected_source["chunk_index"]
    )


def first_relevant_rank(
    results: list[dict[str, Any]],
    item: dict[str, Any],
) -> int | None:
    """
    Return the rank of the first relevant result.
    Rank starts from 1.
    """

    for rank, result in enumerate(results, start=1):
        if is_relevant(result, item):
            return rank

    return None


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    ranked_results: list[list[dict[str, Any]]],
    dataset: list[dict[str, Any]],
) -> dict[str, float]:
    """
    Calculate:
    - Hit@1
    - Hit@3
    - Hit@5
    - MRR
    """

    hit_at_1 = 0
    hit_at_3 = 0
    hit_at_5 = 0
    reciprocal_ranks = []

    for results, item in zip(ranked_results, dataset):
        rank = first_relevant_rank(results, item)

        if rank is not None:
            if rank <= 1:
                hit_at_1 += 1

            if rank <= 3:
                hit_at_3 += 1

            if rank <= 5:
                hit_at_5 += 1

            reciprocal_ranks.append(1.0 / rank)

        else:
            reciprocal_ranks.append(0.0)

    total = len(dataset)

    if total == 0:
        return {
            "Hit@1": 0.0,
            "Hit@3": 0.0,
            "Hit@5": 0.0,
            "MRR": 0.0,
        }

    return {
        "Hit@1": hit_at_1 / total,
        "Hit@3": hit_at_3 / total,
        "Hit@5": hit_at_5 / total,
        "MRR": sum(reciprocal_ranks) / total,
    }


# ============================================================
# COMMON RETRIEVAL PIPELINE
# ============================================================

def retrieve_fixed_k(
    query: str,
    top_k: int,
    dense: DenseRetriever,
    bm25: BM25Retriever,
    hybrid: HybridRetriever,
    reranker: CrossEncoderReranker,
) -> list[dict[str, Any]]:
    """
    Common retrieval pipeline used by BOTH fixed-K
    and adaptive-K experiments.

    Pipeline:

        Dense
          +
        BM25
          ↓
        Hybrid / RRF
          ↓
        Cross-Encoder Reranker
          ↓
        Final Top-K
    """

    dense_results = dense.retrieve(
        query,
        top_k=top_k,
    )

    bm25_results = bm25.retrieve(
        query,
        top_k=top_k,
    )

    hybrid_results = hybrid.fuse(
        [dense_results, bm25_results],
        top_k=top_k,
    )

    reranked_results = reranker.rerank(
        query,
        hybrid_results,
        top_k=min(
            FINAL_TOP_K,
            len(hybrid_results),
        ),
    )

    return reranked_results


# ============================================================
# ADAPTIVE RETRIEVAL
# ============================================================

def retrieve_adaptive(
    query: str,
    adaptive: AdaptiveRetriever,
    dense: DenseRetriever,
    bm25: BM25Retriever,
    hybrid: HybridRetriever,
    reranker: CrossEncoderReranker,
) -> tuple[list[dict[str, Any]], int, str]:
    """
    Adaptive retrieval.

    The ONLY difference from Fixed-K is how top_k is selected:

        Query
          ↓
        Complexity Classifier
          ↓
        Simple / Medium / Complex
          ↓
        K = 5 / 10 / 20
          ↓
        SAME retrieval pipeline as Fixed-K
    """

    complexity_result = adaptive.classifier.classify(query)

    budget = adaptive.get_budget(
        complexity_result.level
    )

    ranked_results = retrieve_fixed_k(
        query=query,
        top_k=budget.top_k,
        dense=dense,
        bm25=bm25,
        hybrid=hybrid,
        reranker=reranker,
    )

    return (
        ranked_results,
        budget.top_k,
        complexity_result.level,
    )


# ============================================================
# PRINTING
# ============================================================

def print_metrics(
    name: str,
    metrics: dict[str, float],
) -> None:
    print(
        f"{name:<15}"
        f"{metrics['Hit@1']:<10.4f}"
        f"{metrics['Hit@3']:<10.4f}"
        f"{metrics['Hit@5']:<10.4f}"
        f"{metrics['MRR']:<10.4f}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    dataset = load_dataset()

    print("=" * 80)
    print("ADAPTIVE RETRIEVAL BENCHMARK")
    print("=" * 80)

    print(f"Dataset: {DATASET_PATH}")
    print(f"Queries: {len(dataset)}")

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Initialize retrieval components ONCE
        # ----------------------------------------------------

        dense = DenseRetriever(db)
        bm25 = BM25Retriever(db)
        hybrid = HybridRetriever()
        reranker = CrossEncoderReranker()

        adaptive = AdaptiveRetriever(db)

        # ----------------------------------------------------
        # Storage for Fixed-K experiments
        # ----------------------------------------------------

        fixed_results: dict[
            int,
            list[list[dict[str, Any]]],
        ] = {}

        # ----------------------------------------------------
        # Storage for Adaptive-K experiment
        # ----------------------------------------------------

        adaptive_ranked_results: list[
            list[dict[str, Any]]
        ] = []

        adaptive_k_values: list[int] = []

        adaptive_complexities: list[str] = []

        complexity_counts = {
            "Simple": 0,
            "Medium": 0,
            "Complex": 0,
        }

        # ====================================================
        # FIXED-K EXPERIMENTS
        # ====================================================

        for top_k in FIXED_K_VALUES:

            print(
                f"\nRunning Fixed-K={top_k}..."
            )

            results = []

            for item in dataset:

                ranked_results = retrieve_fixed_k(
                    query=item["query"],
                    top_k=top_k,
                    dense=dense,
                    bm25=bm25,
                    hybrid=hybrid,
                    reranker=reranker,
                )

                results.append(
                    ranked_results
                )

            fixed_results[top_k] = results

        # ====================================================
        # ADAPTIVE-K EXPERIMENT
        # ====================================================

        print("\nRunning Adaptive-K...")

        for item in dataset:

            (
                ranked_results,
                selected_k,
                complexity,
            ) = retrieve_adaptive(
                query=item["query"],
                adaptive=adaptive,
                dense=dense,
                bm25=bm25,
                hybrid=hybrid,
                reranker=reranker,
            )

            adaptive_ranked_results.append(
                ranked_results
            )

            adaptive_k_values.append(
                selected_k
            )

            adaptive_complexities.append(
                complexity
            )

            complexity_counts[complexity] += 1

        # ====================================================
        # RESULTS
        # ====================================================

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)

        print(
            f"{'Method':<15}"
            f"{'Hit@1':<10}"
            f"{'Hit@3':<10}"
            f"{'Hit@5':<10}"
            f"{'MRR':<10}"
        )

        print("-" * 55)

        # ----------------------------------------------------
        # Fixed-K metrics
        # ----------------------------------------------------

        for top_k in FIXED_K_VALUES:

            metrics = calculate_metrics(
                fixed_results[top_k],
                dataset,
            )

            print_metrics(
                f"Fixed-K={top_k}",
                metrics,
            )

        # ----------------------------------------------------
        # Adaptive-K metrics
        # ----------------------------------------------------

        adaptive_metrics = calculate_metrics(
            adaptive_ranked_results,
            dataset,
        )

        print_metrics(
            "Adaptive-K",
            adaptive_metrics,
        )

        # ====================================================
        # ADAPTIVE STATISTICS
        # ====================================================

        average_k = (
            sum(adaptive_k_values)
            / len(adaptive_k_values)
            if adaptive_k_values
            else 0.0
        )

        print("\n" + "=" * 80)
        print("ADAPTIVE RETRIEVAL STATISTICS")
        print("=" * 80)

        print(
            f"Average selected K: {average_k:.2f}"
        )

        print(
            f"Simple queries: "
            f"{complexity_counts['Simple']}"
        )

        print(
            f"Medium queries: "
            f"{complexity_counts['Medium']}"
        )

        print(
            f"Complex queries: "
            f"{complexity_counts['Complex']}"
        )

        # ====================================================
        # PER-QUERY RESULTS
        # ====================================================

        print("\n" + "=" * 80)
        print("ADAPTIVE RESULTS PER QUERY")
        print("=" * 80)

        for index, item in enumerate(dataset):

            rank = first_relevant_rank(
                adaptive_ranked_results[index],
                item,
            )

            rank_text = (
                str(rank)
                if rank is not None
                else "MISS"
            )

            print(
                f"{index + 1:02d}. "
                f"{item['query_id']} | "
                f"{adaptive_complexities[index]:<7} | "
                f"K={adaptive_k_values[index]:<2} | "
                f"rank={rank_text}"
            )

        # ====================================================
        # K DISTRIBUTION
        # ====================================================

        print("\n" + "=" * 80)
        print("SELECTED K DISTRIBUTION")
        print("=" * 80)

        for k in FIXED_K_VALUES:

            print(
                f"K={k:<2}: "
                f"{adaptive_k_values.count(k)} queries"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()