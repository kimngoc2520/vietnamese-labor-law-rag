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
    relevant_doc_ids: list,
    relevant_articles: list,
) -> bool:
    """
    Kiểm tra chunk có thuộc ground truth hay không.

    Retrieval result lưu document_id và article_title
    ở top-level.

    Ground truth lưu article number, ví dụ:
        "Điều 35"

    Trong database, article_title có thể chứa đầy đủ
    tiêu đề, ví dụ:
        "Điều 35. Quyền đơn phương chấm dứt hợp đồng..."
    """

    doc_id = chunk.get("document_id", "")
    article_title = chunk.get("article_title", "")

    # 1. Kiểm tra Document ID.
    if doc_id not in relevant_doc_ids:
        return False

    # 2. Kiểm tra Article.
    #
    # Ground truth:
    #     "Điều 35"
    #
    # Database:
    #     "Điều 35. Quyền đơn phương chấm dứt..."
    #
    # Vì vậy dùng substring matching.
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
        if is_relevant(
            chunk,
            relevant_doc_ids,
            relevant_articles,
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
                relevant_doc_ids,
                relevant_articles,
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
                relevant_doc_ids,
                relevant_articles,
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
                relevant_doc_ids,
                relevant_articles,
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
                relevant_doc_ids,
                relevant_articles,
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