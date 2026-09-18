import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2]),
)
import json
from pathlib import Path
from typing import Any, Dict, List

from src.db.connection import SessionLocal
from src.retrieval.adaptive import AdaptiveRetriever
from src.retrieval.complexity import QueryComplexityClassifier
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.sparse import BM25Retriever


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "datasets"
    / "retrieval_eval.json"
)

FIXED_K_VALUES = [5, 10, 20]
FINAL_TOP_K = 5


def load_dataset() -> List[Dict[str, Any]]:
    """Load retrieval evaluation dataset."""

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def is_relevant(
    result: Dict[str, Any],
    item: Dict[str, Any],
) -> bool:
    """
    Kiểm tra một retrieved chunk có thuộc ground truth hay không.

    Relevance được xác định bởi:
    - document_id
    - article number
    """

    document_id = result["document_id"]
    article_title = result["article_title"]

    relevant_document_ids = item[
        "relevant_document_ids"
    ]
    relevant_articles = item[
        "relevant_articles"
    ]

    if document_id not in relevant_document_ids:
        return False

    return any(
        article in article_title
        for article in relevant_articles
    )


def first_relevant_rank(
    results: List[Dict[str, Any]],
    item: Dict[str, Any],
) -> int | None:
    """Return 1-based rank of the first relevant result."""

    for rank, result in enumerate(
        results,
        start=1,
    ):
        if is_relevant(result, item):
            return rank

    return None


def calculate_metrics(
    ranked_results: List[List[Dict[str, Any]]],
    dataset: List[Dict[str, Any]],
) -> Dict[str, float]:
    """Calculate Hit@1, Hit@3, Hit@5 and MRR."""

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

    return {
        "Hit@1": hit_at_1 / total,
        "Hit@3": hit_at_3 / total,
        "Hit@5": hit_at_5 / total,
        "MRR": sum(reciprocal_ranks) / total,
    }


def retrieve_fixed_k(
    query: str,
    top_k: int,
    dense: DenseRetriever,
    bm25: BM25Retriever,
    hybrid: HybridRetriever,
    reranker: CrossEncoderReranker,
) -> List[Dict[str, Any]]:
    """
    Run the same retrieval pipeline with a fixed candidate K.
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

    return reranker.rerank(
        query,
        hybrid_results,
        top_k=min(
            FINAL_TOP_K,
            len(hybrid_results),
        ),
    )


def retrieve_adaptive(
    query: str,
    adaptive: AdaptiveRetriever,
) -> tuple[List[Dict[str, Any]], int, str]:
    """
    Run adaptive retrieval.

    Returns:
        final results, selected K, complexity level
    """

    result = adaptive.retrieve(
        query,
        final_top_k=FINAL_TOP_K,
    )

    return (
        result.results,
        result.budget.top_k,
        result.complexity.level,
    )


def print_metrics(
    name: str,
    metrics: Dict[str, float],
) -> None:
    """Print benchmark metrics."""

    print(
        f"{name:<15}"
        f"{metrics['Hit@1']:<10.4f}"
        f"{metrics['Hit@3']:<10.4f}"
        f"{metrics['Hit@5']:<10.4f}"
        f"{metrics['MRR']:<10.4f}"
    )


def main() -> None:
    dataset = load_dataset()

    print("=" * 80)
    print("ADAPTIVE RETRIEVAL BENCHMARK")
    print("=" * 80)

    print(f"Dataset: {DATASET_PATH}")
    print(f"Queries: {len(dataset)}")

    db = SessionLocal()

    try:
        # Shared retrieval components.
        # Models are loaded only once for the whole benchmark.
        dense = DenseRetriever(db)
        bm25 = BM25Retriever(db)
        hybrid = HybridRetriever()
        reranker = CrossEncoderReranker()

        # Adaptive pipeline.
        adaptive = AdaptiveRetriever(db)

        fixed_results = {}
        adaptive_results = []

        # --------------------------------------------------
        # Fixed-K benchmarks
        # --------------------------------------------------

        for top_k in FIXED_K_VALUES:
            print(
                f"\nRunning Fixed-K={top_k}..."
            )

            results = []

            for item in dataset:
                query = item["query"]

                ranked_results = retrieve_fixed_k(
                    query,
                    top_k,
                    dense,
                    bm25,
                    hybrid,
                    reranker,
                )

                results.append(ranked_results)

            fixed_results[top_k] = results

        # --------------------------------------------------
        # Adaptive benchmark
        # --------------------------------------------------

        print("\nRunning Adaptive-K...")

        adaptive_ranked_results = []
        adaptive_k_values = []
        complexity_counts = {
            "Simple": 0,
            "Medium": 0,
            "Complex": 0,
        }

        for item in dataset:
            query = item["query"]

            (
                ranked_results,
                selected_k,
                complexity,
            ) = retrieve_adaptive(
                query,
                adaptive,
            )

            adaptive_ranked_results.append(
                ranked_results
            )

            adaptive_k_values.append(
                selected_k
            )

            complexity_counts[complexity] += 1

        # --------------------------------------------------
        # Metrics
        # --------------------------------------------------

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

        for top_k in FIXED_K_VALUES:
            metrics = calculate_metrics(
                fixed_results[top_k],
                dataset,
            )

            print_metrics(
                f"Fixed-K={top_k}",
                metrics,
            )

        adaptive_metrics = calculate_metrics(
            adaptive_ranked_results,
            dataset,
        )

        print_metrics(
            "Adaptive-K",
            adaptive_metrics,
        )

        # --------------------------------------------------
        # Adaptive statistics
        # --------------------------------------------------

        average_k = sum(
            adaptive_k_values
        ) / len(adaptive_k_values)

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

        print("\nSelected K per query:")

        for index, item in enumerate(
            dataset,
            start=1,
        ):
            query = item["query"]

            (
                _,
                selected_k,
                complexity,
            ) = retrieve_adaptive(
                query,
                adaptive,
            )

            print(
                f"{index:02d}. "
                f"{complexity:<8} "
                f"K={selected_k:<2} "
                f"{query}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()