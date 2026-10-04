# ruff: noqa: E402
import json
import sys
from datetime import datetime, timezone
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

RESULT_PATH = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "adaptive"
    / "quality_cost_benchmark.json"
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
        strict=True,
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
            "Avg K = requested retrieval candidate budget. "
            "Scoring count = fused hybrid candidates passed to "
            "CrossEncoder.predict (all are scored). "
            "Returned top_k after rerank is "
            f"{FINAL_TOP_K}."
        )

        print(
            f"{'Method':<15}"
            f"{'Hit@1':<10}"
            f"{'Hit@3':<10}"
            f"{'Hit@5':<10}"
            f"{'MRR':<10}"
            f"{'Avg K':<10}"
            f"{'Scored':<10}"
        )

        print("-" * 75)

        fixed_payload: dict[str, Any] = {}

        for top_k in FIXED_K_VALUES:
            experiment = fixed_results[top_k]

            metrics = calculate_metrics(
                experiment["ranked_results"],
                dataset,
            )

            total_scoring_count = experiment["total_candidates"]
            average_scoring_count = total_scoring_count / len(dataset)

            print_quality_cost_row(
                f"Fixed-K={top_k}",
                metrics,
                float(top_k),
                total_scoring_count,
            )

            fixed_payload[str(top_k)] = {
                "metrics": metrics,
                "retrieval_candidate_budget": top_k,
                "average_retrieval_candidate_budget": float(top_k),
                "total_reranker_scoring_count": total_scoring_count,
                "average_reranker_scoring_count": average_scoring_count,
                "final_returned_top_k": FINAL_TOP_K,
            }

        adaptive_metrics = calculate_metrics(
            adaptive_ranked_results,
            dataset,
        )

        adaptive_total_scoring_count = sum(adaptive_candidate_counts)
        adaptive_average_budget = (
            sum(adaptive_k_values) / len(adaptive_k_values)
        )
        adaptive_average_scoring_count = (
            adaptive_total_scoring_count / len(dataset)
        )

        print_quality_cost_row(
            "Adaptive-K",
            adaptive_metrics,
            adaptive_average_budget,
            adaptive_total_scoring_count,
        )

        print("\n" + "=" * 90)
        print("ADAPTIVE RERANKER SCORING-COUNT REDUCTION VS FIXED-K")
        print("=" * 90)

        reductions: dict[str, Any] = {}

        for top_k in FIXED_K_VALUES:
            fixed_total = fixed_results[top_k]["total_candidates"]
            saving = 1 - adaptive_total_scoring_count / fixed_total
            reductions[str(top_k)] = {
                "fraction": saving,
                "percent": saving * 100,
                "fixed_total_reranker_scoring_count": fixed_total,
                "adaptive_total_reranker_scoring_count": (
                    adaptive_total_scoring_count
                ),
            }

            print(
                f"vs Fixed-K={top_k}: "
                f"{saving * 100:.2f}% fewer hybrid candidates "
                "scored by the reranker"
            )

        print("\n" + "=" * 90)
        print("ADAPTIVE DISTRIBUTION")
        print("=" * 90)

        complexity_counts = {
            "Simple": 0,
            "Medium": 0,
            "Complex": 0,
        }

        for complexity in adaptive_complexities:
            complexity_counts[complexity] += 1

        k_distribution: dict[str, int] = {
            str(k): 0 for k in FIXED_K_VALUES
        }

        for selected_k in adaptive_k_values:
            key = str(selected_k)
            k_distribution[key] = k_distribution.get(key, 0) + 1

        print(f"Simple:   {complexity_counts['Simple']}")
        print(f"Medium:   {complexity_counts['Medium']}")
        print(f"Complex:  {complexity_counts['Complex']}")
        print(f"Average retrieval candidate budget: {adaptive_average_budget:.2f}")

        print("\n" + "=" * 90)
        print("ADAPTIVE PER-QUERY")
        print("=" * 90)

        per_query: list[dict[str, Any]] = []

        for index, item in enumerate(dataset):
            rank = first_relevant_rank(
                adaptive_ranked_results[index],
                item,
            )
            rank_text = str(rank) if rank is not None else "MISS"
            record = {
                "query_id": item["query_id"],
                "complexity": adaptive_complexities[index],
                "retrieval_candidate_budget": adaptive_k_values[index],
                "reranker_scoring_count": adaptive_candidate_counts[index],
                "relevant_rank": rank,
            }
            per_query.append(record)

            print(
                f"{item['query_id']} | "
                f"{adaptive_complexities[index]:<7} | "
                f"K={adaptive_k_values[index]:<2} | "
                f"scored="
                f"{adaptive_candidate_counts[index]:<2} | "
                f"rank={rank_text}"
            )

        payload = {
            "benchmark": "quality_cost",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "query_count": len(dataset),
            "final_returned_top_k": FINAL_TOP_K,
            "fixed_k_values": FIXED_K_VALUES,
            "terminology": {
                "retrieval_candidate_budget": (
                    "Requested dense/BM25/hybrid top_k for the query."
                ),
                "reranker_scoring_count": (
                    "Number of fused hybrid candidates passed to "
                    "CrossEncoder.predict; all of these documents "
                    "are scored."
                ),
                "final_returned_top_k": (
                    "Number of documents returned after reranking, "
                    "not the number scored."
                ),
            },
            "fixed_k": fixed_payload,
            "adaptive": {
                "metrics": adaptive_metrics,
                "average_retrieval_candidate_budget": adaptive_average_budget,
                "total_reranker_scoring_count": adaptive_total_scoring_count,
                "average_reranker_scoring_count": (
                    adaptive_average_scoring_count
                ),
                "complexity_counts": complexity_counts,
                "k_distribution": k_distribution,
                "final_returned_top_k": FINAL_TOP_K,
            },
            "reranker_scoring_count_reduction_vs_fixed_k": reductions,
            "per_query": per_query,
        }

        RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESULT_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nSaved: {RESULT_PATH}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
