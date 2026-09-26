import json
import sys
from pathlib import Path
from typing import Any

# evaluation/scripts/run_quality_cost_benchmark.py
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
# GROUND-TRUTH
# ============================================================

def is_relevant(
    result: dict[str, Any],
    item: dict[str, Any],
) -> bool:
    expected_source = item["source"]

    return (
        result["document_id"] == expected_source["document_id"]
        and result["chunk_index"] == expected_source["chunk_index"]
    )


def first_relevant_rank(
    results: list[dict[str, Any]],
    item: dict[str, Any],
) -> int | None:

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

    hit_at_1 = 0
    hit_at_3 = 0
    hit_at_5 = 0
    reciprocal_ranks = []

    for results, item in zip(
        ranked_results,
        dataset,
    ):

        rank = first_relevant_rank(
            results,
            item,
        )

        if rank is not None:

            if rank <= 1:
                hit_at_1 += 1

            if rank <= 3:
                hit_at_3 += 1

            if rank <= 5:
                hit_at_5 += 1

            reciprocal_ranks.append(
                1.0 / rank
            )

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
) -> tuple[list[dict[str, Any]], int]:

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

    candidate_count = len(hybrid_results)

    reranked_results = reranker.rerank(
        query,
        hybrid_results,
        top_k=min(
            FINAL_TOP_K,
            len(hybrid_results),
        ),
    )

    return (
        reranked_results,
        candidate_count,
    )


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
) -> tuple[list[dict[str, Any]], int, str, int]:

    complexity_result = adaptive.classifier.classify(
        query
    )

    budget = adaptive.get_budget(
        complexity_result.level
    )

    ranked_results, candidate_count = retrieve_fixed_k(
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
        candidate_count,
    )


# ============================================================
# REPORTING
# ============================================================

def print_quality_cost_row(
    name: str,
    metrics: dict[str, float],
    average_k: float,
    total_candidates: int,
) -> None:

    print(
        f"{name:<15}"
        f"{metrics['Hit@1']:<10.4f}"
        f"{metrics['Hit@3']:<10.4f}"
        f"{metrics['Hit@5']:<10.4f}"
        f"{metrics['MRR']:<10.4f}"
        f"{average_k:<10.2f}"
        f"{total_candidates:<10}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    dataset = load_dataset()

    print("=" * 90)
    print("QUALITY-COST BENCHMARK")
    print("=" * 90)

    print(f"Dataset: {DATASET_PATH}")
    print(f"Queries: {len(dataset)}")

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Initialize components once
        # ----------------------------------------------------

        dense = DenseRetriever(db)
        bm25 = BM25Retriever(db)
        hybrid = HybridRetriever()
        reranker = CrossEncoderReranker()

        adaptive = AdaptiveRetriever(db)

        # ====================================================
        # FIXED-K
        # ====================================================

        fixed_results = {}

        for top_k in FIXED_K_VALUES:

            print(
                f"\nRunning Fixed-K={top_k}..."
            )

            ranked_results = []
            total_candidates = 0

            for item in dataset:

                results, candidate_count = retrieve_fixed_k(
                    query=item["query"],
                    top_k=top_k,
                    dense=dense,
                    bm25=bm25,
                    hybrid=hybrid,
                    reranker=reranker,
                )

                ranked_results.append(
                    results
                )

                total_candidates += candidate_count

            fixed_results[top_k] = {
                "ranked_results": ranked_results,
                "total_candidates": total_candidates,
            }

        # ====================================================
        # ADAPTIVE-K
        # ====================================================

        print("\nRunning Adaptive-K...")

        adaptive_ranked_results = []

        adaptive_k_values = []

        adaptive_complexities = []

        adaptive_candidate_counts = []

        for item in dataset:

            (
                results,
                selected_k,
                complexity,
                candidate_count,
            ) = retrieve_adaptive(
                query=item["query"],
                adaptive=adaptive,
                dense=dense,
                bm25=bm25,
                hybrid=hybrid,
                reranker=reranker,
            )

            adaptive_ranked_results.append(
                results
            )

            adaptive_k_values.append(
                selected_k
            )

            adaptive_complexities.append(
                complexity
            )

            adaptive_candidate_counts.append(
                candidate_count
            )

        # ====================================================
        # QUALITY-COST RESULTS
        # ====================================================

        print("\n" + "=" * 90)
        print("QUALITY-COST RESULTS")
        print("=" * 90)

        print(
            f"{'Method':<15}"
            f"{'Hit@1':<10}"
            f"{'Hit@3':<10}"
            f"{'Hit@5':<10}"
            f"{'MRR':<10}"
            f"{'Avg K':<10}"
            f"{'Candidates':<10}"
        )

        print("-" * 75)

        # ----------------------------------------------------
        # Fixed-K metrics
        # ----------------------------------------------------

        for top_k in FIXED_K_VALUES:

            experiment = fixed_results[top_k]

            metrics = calculate_metrics(
                experiment["ranked_results"],
                dataset,
            )

            total_candidates = experiment[
                "total_candidates"
            ]

            average_k = (
                total_candidates
                / len(dataset)
            )

            print_quality_cost_row(
                f"Fixed-K={top_k}",
                metrics,
                average_k,
                total_candidates,
            )

        # ----------------------------------------------------
        # Adaptive metrics
        # ----------------------------------------------------

        adaptive_metrics = calculate_metrics(
            adaptive_ranked_results,
            dataset,
        )

        adaptive_total_candidates = sum(
            adaptive_candidate_counts
        )

        adaptive_average_k = (
            sum(adaptive_k_values)
            / len(adaptive_k_values)
        )

        print_quality_cost_row(
            "Adaptive-K",
            adaptive_metrics,
            adaptive_average_k,
            adaptive_total_candidates,
        )

        # ====================================================
        # COST SAVING
        # ====================================================

        print("\n" + "=" * 90)
        print("ADAPTIVE COST SAVING VS FIXED-K")
        print("=" * 90)

        for top_k in FIXED_K_VALUES:

            fixed_total = fixed_results[
                top_k
            ]["total_candidates"]

            saving = (
                1
                - adaptive_total_candidates
                / fixed_total
            )

            print(
                f"vs Fixed-K={top_k}: "
                f"{saving * 100:.2f}% "
                f"fewer candidates"
            )

        # ====================================================
        # ADAPTIVE DISTRIBUTION
        # ====================================================

        print("\n" + "=" * 90)
        print("ADAPTIVE DISTRIBUTION")
        print("=" * 90)

        complexity_counts = {
            "Simple": 0,
            "Medium": 0,
            "Complex": 0,
        }

        for complexity in adaptive_complexities:

            complexity_counts[
                complexity
            ] += 1

        print(
            f"Simple:   "
            f"{complexity_counts['Simple']}"
        )

        print(
            f"Medium:   "
            f"{complexity_counts['Medium']}"
        )

        print(
            f"Complex:  "
            f"{complexity_counts['Complex']}"
        )

        print(
            f"Average K: "
            f"{adaptive_average_k:.2f}"
        )

        # ====================================================
        # PER-QUERY COST
        # ====================================================

        print("\n" + "=" * 90)
        print("ADAPTIVE PER-QUERY COST")
        print("=" * 90)

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
                f"{item['query_id']} | "
                f"{adaptive_complexities[index]:<7} | "
                f"K={adaptive_k_values[index]:<2} | "
                f"candidates="
                f"{adaptive_candidate_counts[index]:<2} | "
                f"rank={rank_text}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()