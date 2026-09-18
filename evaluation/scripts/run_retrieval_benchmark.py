import sys
import os
import json
from pathlib import Path

# Thêm thư mục gốc vào path để import được src
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from src.db.connection import SessionLocal
from src.retrieval.dense import DenseRetriever
from src.retrieval.reranker import CrossEncoderReranker


def is_relevant(
    chunk: dict,
    relevant_doc_ids: list,
    relevant_articles: list,
) -> bool:
    """Kiểm tra một chunk có thuộc tập relevant (ground truth) hay không."""

    # DenseRetriever trả document_id và article_title ở top-level
    # của chunk result, không nằm bên trong metadata.
    doc_id = chunk.get("document_id", "")
    article_title = chunk.get("article_title", "")

    # 1. Kiểm tra Document ID
    if doc_id not in relevant_doc_ids:
        return False

    # 2. Kiểm tra Article nếu ground truth có chỉ định
    if relevant_articles:
        return any(
            article in article_title
            for article in relevant_articles
        )

    return True


def calculate_metrics(
    retrieved_chunks: list,
    relevant_doc_ids: list,
    relevant_articles: list,
    k_values: list,
):
    """Tính Hit Rate@K và MRR."""

    hit_at_k = {k: 0.0 for k in k_values}
    first_relevant_rank = None

    for rank, chunk in enumerate(retrieved_chunks, 1):
        if is_relevant(
            chunk,
            relevant_doc_ids,
            relevant_articles,
        ):
            if first_relevant_rank is None:
                first_relevant_rank = rank

            # Nếu có relevant chunk trong Top-K
            # thì Hit@K = 1.
            for k in k_values:
                if rank <= k:
                    hit_at_k[k] = 1.0

    # MRR = 1 / rank của relevant result đầu tiên.
    # Nếu không tìm thấy relevant result thì MRR = 0.
    mrr = (
        1.0 / first_relevant_rank
        if first_relevant_rank is not None
        else 0.0
    )

    return hit_at_k, mrr


def run_benchmark():
    print(" Bắt đầu Benchmark Retrieval Pipeline...\n")

    # 1. Load evaluation dataset
    dataset_path = Path(
        "evaluation/datasets/retrieval_eval.json"
    )

    if not dataset_path.exists():
        print(f" Không tìm thấy file: {dataset_path}")
        return

    with dataset_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        eval_data = json.load(file)

    print(
        f" Loaded {len(eval_data)} evaluation queries.\n"
    )

    db = SessionLocal()

    try:
        dense_retriever = DenseRetriever(db)
        reranker = CrossEncoderReranker()

        k_values = [1, 3, 5]

        # Accumulator cho hai pipeline
        metrics = {
            "dense": {
                "hit_rate": {
                    k: 0.0 for k in k_values
                },
                "mrr_sum": 0.0,
            },
            "reranked": {
                "hit_rate": {
                    k: 0.0 for k in k_values
                },
                "mrr_sum": 0.0,
            },
        }

        # 2. Chạy từng evaluation query
        for i, item in enumerate(eval_data, 1):
            query = item["query"]
            relevant_doc_ids = item[
                "relevant_document_ids"
            ]
            relevant_articles = item[
                "relevant_articles"
            ]

            print(
                f"[{i}/{len(eval_data)}] "
                f"Query: '{query[:60]}...'"
            )

            # -------------------------------------------------
            # Pipeline 1: Dense Retrieval
            # -------------------------------------------------
            dense_results = dense_retriever.retrieve(
                query,
                top_k=10,
            )

            dense_hits, dense_mrr = calculate_metrics(
                dense_results,
                relevant_doc_ids,
                relevant_articles,
                k_values,
            )

            for k in k_values:
                metrics["dense"]["hit_rate"][k] += (
                    dense_hits[k]
                )

            metrics["dense"]["mrr_sum"] += dense_mrr

            # -------------------------------------------------
            # Pipeline 2: Dense + Reranker
            # -------------------------------------------------
            reranked_results = reranker.rerank(
                query,
                dense_results,
                top_k=5,
            )

            rerank_hits, rerank_mrr = calculate_metrics(
                reranked_results,
                relevant_doc_ids,
                relevant_articles,
                k_values,
            )

            for k in k_values:
                metrics["reranked"]["hit_rate"][k] += (
                    rerank_hits[k]
                )

            metrics["reranked"]["mrr_sum"] += rerank_mrr

        # 3. Tính trung bình
        num_queries = len(eval_data)

        if num_queries == 0:
            print(" Evaluation dataset không có query.")
            return

        print("\n" + "=" * 75)
        print(" KẾT QUẢ BENCHMARK RETRIEVAL")
        print("=" * 75)

        print(
            f"{'Metric':<15} | "
            f"{'Dense Only (Top 10)':<25} | "
            f"{'Dense + Reranker (Top 5)':<25}"
        )

        print("-" * 75)

        for k in k_values:
            dense_hr = (
                metrics["dense"]["hit_rate"][k]
                / num_queries
            )

            rerank_hr = (
                metrics["reranked"]["hit_rate"][k]
                / num_queries
            )

            print(
                f"{'Hit Rate@' + str(k):<15} | "
                f"{dense_hr:<25.4f} | "
                f"{rerank_hr:<25.4f}"
            )

        dense_mrr_avg = (
            metrics["dense"]["mrr_sum"]
            / num_queries
        )

        rerank_mrr_avg = (
            metrics["reranked"]["mrr_sum"]
            / num_queries
        )

        print(
            f"{'MRR':<15} | "
            f"{dense_mrr_avg:<25.4f} | "
            f"{rerank_mrr_avg:<25.4f}"
        )

        print("=" * 75)

        print(
            "\n Benchmark hoàn tất!"
        )
        print(
            "Kết quả này sẽ được dùng làm baseline "
            "để so sánh với Hybrid/Adaptive sau này."
        )

    finally:
        db.close()


if __name__ == "__main__":
    run_benchmark()