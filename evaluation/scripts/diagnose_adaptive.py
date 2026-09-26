"""
Diagnostic script cho Adaptive Retrieval.

Mục đích:
    1. Kiểm tra phân bố complexity trên evaluation set.
    2. Kiểm tra Adaptive K được chọn cho từng query.
    3. Đo vị trí EXACT ground-truth chunk trong candidate list:
        - Fixed K = 5
        - Fixed K = 10
        - Fixed K = 20
        - Adaptive K
    4. Đo rank trước rerank và sau rerank.
    5. Kiểm tra candidate coverage của exact ground-truth chunk.
    6. Xuất kết quả chi tiết ra CSV.

Ground truth được xác định chính xác bằng:

    document_id + chunk_index

Không dùng article-level substring matching để tránh trường hợp
"Điều 3" bị match nhầm với "Điều 35".

Cách chạy:

    docker compose exec api python evaluation/scripts/diagnose_adaptive.py

Output:

    evaluation/reports/adaptive_diagnostic.csv
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)


# ============================================================
# REPO IMPORTS
# ============================================================

from src.db.connection import SessionLocal
from src.retrieval.adaptive import AdaptiveRetriever
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.sparse import BM25Retriever

# ============================================================
# PATHS
# ============================================================

DATASET_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "datasets"
    / "retrieval_eval.json"
)

GT_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "datasets"
    / "ground_truth_evidence.json"
)

OUT_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "reports"
    / "adaptive_diagnostic.csv"
)


# ============================================================
# CONFIG
# ============================================================

FIXED_K_VALUES = [5, 10, 20]

# Same final output size as current adaptive benchmark.
FINAL_TOP_K = 5


# ============================================================
# DATA LOADING
# ============================================================

def load_dataset() -> tuple[
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    """
    Load evaluation dataset and exact ground-truth evidence.

    retrieval_eval.json hiện không có query_id.

    ground_truth_evidence.json có:
        Q01, Q02, ..., Q10

    Hai file được ghép theo thứ tự query.

    Returns:
        dataset:
            Evaluation queries.

        gt_map:
            query_id -> exact ground-truth source.
    """

    # --------------------------------------------------------
    # Load retrieval evaluation dataset
    # --------------------------------------------------------

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        dataset = json.load(file)

    # --------------------------------------------------------
    # Load provenance-backed ground truth
    # --------------------------------------------------------

    with GT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        ground_truth = json.load(file)

    # --------------------------------------------------------
    # Validate dataset size
    # --------------------------------------------------------

    if len(dataset) != len(ground_truth):
        raise ValueError(
            "retrieval_eval.json và "
            "ground_truth_evidence.json "
            f"không cùng số lượng query: "
            f"{len(dataset)} != {len(ground_truth)}"
        )

    # --------------------------------------------------------
    # Build mapping
    #
    # retrieval_eval[0] -> Q01
    # retrieval_eval[1] -> Q02
    # ...
    # retrieval_eval[9] -> Q10
    #
    # Không sửa file retrieval_eval.json.
    # --------------------------------------------------------

    gt_map: dict[str, dict[str, Any]] = {}

    for index, (query_item, gt_item) in enumerate(
        zip(dataset, ground_truth),
        start=1,
    ):
        query_id = gt_item["query_id"]

        # ----------------------------------------------------
        # Sanity check:
        # đảm bảo query trong hai file thực sự tương ứng.
        # ----------------------------------------------------

        if (
            query_item["query"].strip()
            != gt_item["query"].strip()
        ):
            raise ValueError(
                f"Query mismatch tại vị trí {index}: "
                f"{query_id}"
            )

        gt_map[query_id] = gt_item["source"]

        # ----------------------------------------------------
        # Gắn query_id vào object trong memory.
        #
        # Chỉ phục vụ diagnostic.
        # Không ghi ngược vào JSON.
        # ----------------------------------------------------

        query_item["query_id"] = query_id

    return dataset, gt_map


# ============================================================
# EXACT CHUNK IDENTITY
# ============================================================

def get_chunk_key(
    result: dict[str, Any],
) -> tuple[str, int]:
    """
    Return exact identity of a retrieved chunk.

    A chunk is uniquely identified by:

        document_id + chunk_index
    """

    return (
        result["document_id"],
        result["chunk_index"],
    )


def find_ground_truth_rank(
    results: list[dict[str, Any]],
    gt_source: dict[str, Any],
) -> int | None:
    """
    Find the 1-based rank of the exact ground-truth chunk.

    Returns:
        rank:
            1-based rank if the exact GT chunk exists.

        None:
            GT chunk is not present in the ranked list.
    """

    gt_key = (
        gt_source["document_id"],
        gt_source["chunk_index"],
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):
        if get_chunk_key(result) == gt_key:
            return rank

    return None


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_candidates_pre_rerank(
    query: str,
    top_k: int,
    dense: DenseRetriever,
    bm25: BM25Retriever,
    hybrid: HybridRetriever,
) -> list[dict[str, Any]]:
    """
    Run retrieval pipeline up to Hybrid/RRF.

    Pipeline:

        Dense
          +
        BM25
          ↓
        Hybrid / RRF

    Returned list is the candidate pool BEFORE reranking.
    """

    # --------------------------------------------------------
    # Dense retrieval
    # --------------------------------------------------------

    dense_results = dense.retrieve(
        query,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # BM25 retrieval
    # --------------------------------------------------------

    bm25_results = bm25.retrieve(
        query,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # Hybrid / RRF
    # --------------------------------------------------------

    hybrid_results = hybrid.fuse(
        [
            dense_results,
            bm25_results,
        ],
        top_k=top_k,
    )

    return hybrid_results


# ============================================================
# RERANKING
# ============================================================

def rerank_candidates(
    query: str,
    candidates: list[dict[str, Any]],
    reranker: CrossEncoderReranker,
) -> list[dict[str, Any]]:
    """
    Rerank candidate pool.

    Same final Top-K behavior as current benchmark.
    """

    return reranker.rerank(
        query,
        candidates,
        top_k=min(
            FINAL_TOP_K,
            len(candidates),
        ),
    )


# ============================================================
# FORMATTING
# ============================================================

def format_rank(
    value: int | None,
) -> str:
    """
    Format rank for console output.
    """

    if value is None:
        return "-"

    return str(value)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    dataset, gt_map = load_dataset()

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    db = SessionLocal()

    rows: list[dict[str, Any]] = []

    complexity_counter = {
        "Simple": 0,
        "Medium": 0,
        "Complex": 0,
    }

    try:

        # ====================================================
        # Initialize retrieval components once
        # ====================================================

        dense = DenseRetriever(db)

        bm25 = BM25Retriever(db)

        hybrid = HybridRetriever()

        reranker = CrossEncoderReranker()

        adaptive = AdaptiveRetriever(db)

        # ====================================================
        # Header
        # ====================================================

        print()
        print("=" * 130)
        print("ADAPTIVE RETRIEVAL DIAGNOSTIC")
        print("=" * 130)

        print(
            f"Dataset : {DATASET_PATH}"
        )

        print(
            f"GT file : {GT_PATH}"
        )

        print(
            f"Queries : {len(dataset)}"
        )

        print()

        # ----------------------------------------------------
        # Table header
        # ----------------------------------------------------

        header = (
            f"{'#':<4}"
            f"{'QID':<6}"
            f"{'GT chunk':<18}"
            f"{'Complexity':<12}"
            f"{'Score':<8}"
            f"{'Adap K':<8}"
        )

        for k in FIXED_K_VALUES:

            header += (
                f"{'K' + str(k) + ' pre':<10}"
                f"{'K' + str(k) + ' post':<11}"
            )

        header += (
            f"{'Adap pre':<10}"
            f"{'Adap post':<10}"
        )

        print(header)
        print("-" * len(header))

        # ====================================================
        # Process every query
        # ====================================================

        for index, item in enumerate(
            dataset,
            start=1,
        ):

            # ------------------------------------------------
            # Query
            # ------------------------------------------------

            query_id = item["query_id"]

            query = item["query"]

            # ------------------------------------------------
            # Ground truth
            # ------------------------------------------------

            if query_id not in gt_map:

                print(
                    f"[WARN] Missing ground truth: "
                    f"{query_id}"
                )

                continue

            gt_source = gt_map[query_id]

            # ------------------------------------------------
            # Adaptive Retrieval
            #
            # Run once here so we can inspect:
            #
            # adaptive_result.candidates
            # adaptive_result.results
            # adaptive_result.complexity
            # adaptive_result.budget
            # ------------------------------------------------

            adaptive_result = adaptive.retrieve(
                query,
                final_top_k=FINAL_TOP_K,
            )

            # ------------------------------------------------
            # Complexity
            # ------------------------------------------------

            complexity = (
                adaptive_result
                .complexity
                .level
            )

            complexity_score = (
                adaptive_result
                .complexity
                .score
            )

            # ------------------------------------------------
            # Adaptive K
            # ------------------------------------------------

            adaptive_k = (
                adaptive_result
                .budget
                .top_k
            )

            complexity_counter[
                complexity
            ] = complexity_counter.get(
                complexity,
                0,
            ) + 1

            # ------------------------------------------------
            # Initialize row
            # ------------------------------------------------

            row: dict[str, Any] = {
                "index": index,
                "query_id": query_id,
                "query": query,
                "gt_document_id": gt_source[
                    "document_id"
                ],
                "gt_chunk_index": gt_source[
                    "chunk_index"
                ],
                "gt_article": gt_source[
                    "article"
                ],
                "complexity": complexity,
                "complexity_score": (
                    complexity_score
                ),
                "adaptive_k": adaptive_k,
            }

            # =================================================
            # FIXED K
            # =================================================

            for k in FIXED_K_VALUES:

                # ------------------------------------------------
                # Candidate pool BEFORE reranking
                # ------------------------------------------------

                candidates = (
                    retrieve_candidates_pre_rerank(
                        query,
                        k,
                        dense,
                        bm25,
                        hybrid,
                    )
                )

                # ------------------------------------------------
                # Exact GT rank BEFORE reranking
                # ------------------------------------------------

                pre_rank = (
                    find_ground_truth_rank(
                        candidates,
                        gt_source,
                    )
                )

                # ------------------------------------------------
                # Rerank
                # ------------------------------------------------

                reranked = rerank_candidates(
                    query,
                    candidates,
                    reranker,
                )

                # ------------------------------------------------
                # Exact GT rank AFTER reranking
                # ------------------------------------------------

                post_rank = (
                    find_ground_truth_rank(
                        reranked,
                        gt_source,
                    )
                )

                # ------------------------------------------------
                # Store
                # ------------------------------------------------

                row[
                    f"K{k}_pre_rank"
                ] = pre_rank

                row[
                    f"K{k}_post_rank"
                ] = post_rank

            # =================================================
            # ADAPTIVE K
            # =================================================

            # ------------------------------------------------
            # Exact GT rank BEFORE reranking
            # ------------------------------------------------

            adaptive_pre_rank = (
                find_ground_truth_rank(
                    adaptive_result.candidates,
                    gt_source,
                )
            )

            # ------------------------------------------------
            # Exact GT rank AFTER reranking
            # ------------------------------------------------

            adaptive_post_rank = (
                find_ground_truth_rank(
                    adaptive_result.results,
                    gt_source,
                )
            )

            row[
                "adaptive_pre_rank"
            ] = adaptive_pre_rank

            row[
                "adaptive_post_rank"
            ] = adaptive_post_rank

            rows.append(row)

            # =================================================
            # Console output
            # =================================================

            gt_label = (
                f"{gt_source['document_id']}:"
                f"{gt_source['chunk_index']}"
            )

            line = (
                f"{index:<4}"
                f"{query_id:<6}"
                f"{gt_label:<18}"
                f"{complexity:<12}"
                f"{complexity_score:<8.1f}"
                f"{adaptive_k:<8}"
            )

            for k in FIXED_K_VALUES:

                line += (
                    f"{format_rank(row[f'K{k}_pre_rank']):<10}"
                    f"{format_rank(row[f'K{k}_post_rank']):<11}"
                )

            line += (
                f"{format_rank(adaptive_pre_rank):<10}"
                f"{format_rank(adaptive_post_rank):<10}"
            )

            print(line)

        # ====================================================
        # COMPLEXITY DISTRIBUTION
        # ====================================================

        print()
        print("=" * 70)
        print("COMPLEXITY DISTRIBUTION")
        print("=" * 70)

        for level in [
            "Simple",
            "Medium",
            "Complex",
        ]:

            count = complexity_counter[
                level
            ]

            print(
                f"{level:<10}: "
                f"{count}/{len(rows)}"
            )

        # ====================================================
        # ADAPTIVE K DISTRIBUTION
        # ====================================================

        adaptive_k_counter: dict[int, int] = {}

        for row in rows:

            k = row["adaptive_k"]

            adaptive_k_counter[k] = (
                adaptive_k_counter.get(
                    k,
                    0,
                )
                + 1
            )

        print()
        print("=" * 70)
        print("ADAPTIVE K DISTRIBUTION")
        print("=" * 70)

        for k in sorted(
            adaptive_k_counter
        ):

            count = adaptive_k_counter[k]

            print(
                f"K={k:<3}: "
                f"{count}/{len(rows)}"
            )

        # ====================================================
        # AVERAGE ADAPTIVE K
        # ====================================================

        adaptive_k_values = [
            row["adaptive_k"]
            for row in rows
        ]

        if adaptive_k_values:

            average_adaptive_k = (
                sum(adaptive_k_values)
                / len(adaptive_k_values)
            )

            print()
            print(
                f"Average Adaptive K: "
                f"{average_adaptive_k:.2f}"
            )

        # ====================================================
        # EXACT GT CANDIDATE COVERAGE
        # ====================================================

        print()
        print("=" * 70)
        print("EXACT GT CANDIDATE COVERAGE")
        print("=" * 70)

        for k in FIXED_K_VALUES:

            found = sum(
                row[f"K{k}_pre_rank"]
                is not None
                for row in rows
            )

            print(
                f"K={k:<3}: "
                f"{found}/{len(rows)} "
                f"({found / len(rows):.1%})"
            )

        adaptive_found = sum(
            row["adaptive_pre_rank"]
            is not None
            for row in rows
        )

        print(
            f"Adaptive: "
            f"{adaptive_found}/{len(rows)} "
            f"({adaptive_found / len(rows):.1%})"
        )

        # ====================================================
        # CSV
        # ====================================================

        OUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fieldnames = [
            "index",
            "query_id",
            "query",
            "gt_document_id",
            "gt_chunk_index",
            "gt_article",
            "complexity",
            "complexity_score",
            "adaptive_k",
        ]

        for k in FIXED_K_VALUES:

            fieldnames.extend(
                [
                    f"K{k}_pre_rank",
                    f"K{k}_post_rank",
                ]
            )

        fieldnames.extend(
            [
                "adaptive_pre_rank",
                "adaptive_post_rank",
            ]
        )

        with OUT_PATH.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            writer.writerows(rows)

        print()
        print(
            f"Diagnostic CSV: {OUT_PATH}"
        )

        # ====================================================
        # INTERPRETATION GUIDE
        # ====================================================

        print()
        print("=" * 70)
        print("HOW TO READ THIS DIAGNOSTIC")
        print("=" * 70)

        print(
            "1. Nếu complexity dồn vào một mức duy nhất:"
        )

        print(
            "   Adaptive đang ít tạo ra sự khác biệt "
            "về candidate budget."
        )

        print()

        print(
            "2. Nếu exact GT thường đã xuất hiện ở K=5:"
        )

        print(
            "   Candidate retrieval có dấu hiệu "
            "bão hòa sớm ở K=5."
        )

        print()

        print(
            "3. Nếu GT chỉ xuất hiện từ K=10 hoặc K=20:"
        )

        print(
            "   Candidate expansion thực sự có khả năng "
            "mở thêm cơ hội retrieval."
        )

        print()

        print(
            "4. Nếu pre-rank và post-rank khác nhau:"
        )

        print(
            "   Cross-Encoder reranker đang thay đổi "
            "thứ hạng của candidate."
        )

        print()

        print(
            "5. Nếu Adaptive pre/post trùng với Fixed K "
            "tương ứng:"
        )

        print(
            "   AdaptiveRetriever đang thực hiện đúng "
            "budget đã chọn."
        )

        print()

        print(
            "6. Không kết luận Adaptive tốt/xấu chỉ từ "
            "10 queries."
        )

        print(
            "   Diagnostic này dùng để xác định "
            "vì sao K=5/10/20 đang cho kết quả giống nhau."
        )

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()