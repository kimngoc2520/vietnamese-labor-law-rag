from dataclasses import dataclass
from typing import Any, ClassVar

from sqlalchemy.orm import Session

from src.retrieval.complexity import (
    ComplexityResult,
    QueryComplexityClassifier,
)
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.sparse import BM25Retriever


def _apply_subject_boost(
    query: str,
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Điều chỉnh nhẹ rerank score dựa trên subject của query.

    Mục đích:
        Cross-Encoder có thể cho điểm rất gần nhau giữa các điều
        có cùng cụm từ pháp lý nhưng khác chủ thể.

    Ví dụ:
        Query:
            "Người lao động có quyền đơn phương chấm dứt
             hợp đồng lao động trong những trường hợp nào?"

        Có thể xảy ra:
            Điều 36 (người sử dụng lao động) > Điều 35 (người lao động)

        Subject boost giúp ưu tiên chunk có cùng subject với query
        mà không hard-code một điều luật cụ thể.

    Args:
        query:
            Câu hỏi của người dùng.

        results:
            Danh sách kết quả sau Cross-Encoder reranking.

    Returns:
        Danh sách kết quả sau subject-aware adjustment,
        được sắp xếp lại theo rerank_score.
    """

    query_lower = query.lower()

    # Kiểm tra subject cụ thể trước để tránh:
    # "người sử dụng lao động" bị match nhầm vào
    # "người lao động".
    if "người sử dụng lao động" in query_lower:
        subject_term = "người sử dụng lao động"
    elif "người lao động" in query_lower:
        subject_term = "người lao động"
    else:
        return results

    for result in results:
        content = result.get("content", "").lower()
        article_title = result.get(
            "article_title",
            "",
        ).lower()

        searchable_text = (
            f"{article_title} {content}"
        )

        if subject_term in searchable_text:
            result["rerank_score"] = (
                result.get("rerank_score", 0.0)
                + 0.001
            )

    return sorted(
        results,
        key=lambda x: x.get(
            "rerank_score",
            0.0,
        ),
        reverse=True,
    )


@dataclass(frozen=True)
class RetrievalBudget:
    """
    Retrieval budget được chọn dựa trên query complexity.
    """

    complexity: str
    top_k: int


@dataclass
class AdaptiveRetrievalResult:
    """
    Kết quả của toàn bộ adaptive retrieval pipeline.

    Attributes:
        complexity:
            Kết quả phân loại độ phức tạp của query.

        budget:
            Retrieval budget được chọn cho query.

        candidates:
            Candidate pool sau hybrid retrieval.

        results:
            Các kết quả cuối cùng sau reranking.
    """

    complexity: ComplexityResult
    budget: RetrievalBudget
    candidates: list[dict[str, Any]]
    results: list[dict[str, Any]]


class AdaptiveRetriever:
    """
    Adaptive Retrieval pipeline.

    Flow:

        Query
          ↓
        Query Complexity Classifier
          ↓
        Adaptive Top-K
          ↓
        Dense Retrieval + BM25
          ↓
        Hybrid Retrieval (RRF)
          ↓
        Cross-Encoder Reranking
          ↓
        Subject-aware Adjustment
          ↓
        Final Results

    MVP policy:

        Simple   → top_k = 5
        Medium   → top_k = 10
        Complex  → top_k = 20
    """

    TOP_K_BY_COMPLEXITY: ClassVar[dict[str, int]] = {
        "Simple": 5,
        "Medium": 10,
        "Complex": 20,
    }

    FINAL_TOP_K: ClassVar[int] = 5

    def __init__(self, db_session: Session):
        """
        Khởi tạo adaptive retrieval pipeline.

        Args:
            db_session:
                SQLAlchemy session kết nối PostgreSQL.
        """

        self.classifier = QueryComplexityClassifier()

        self.dense = DenseRetriever(db_session)

        self.bm25 = BM25Retriever(db_session)

        self.hybrid = HybridRetriever()

        self.reranker = CrossEncoderReranker()

    def get_budget(
        self,
        complexity: str,
    ) -> RetrievalBudget:
        """
        Chuyển complexity level thành retrieval budget.

        Args:
            complexity:
                Simple, Medium hoặc Complex.

        Returns:
            RetrievalBudget chứa complexity và top_k.
        """

        if not complexity or not complexity.strip():
            raise ValueError(
                "Complexity không được để trống."
            )

        normalized_complexity = (
            complexity.strip().capitalize()
        )

        if normalized_complexity not in (
            self.TOP_K_BY_COMPLEXITY
        ):
            raise ValueError(
                "Complexity không hợp lệ. "
                "Giá trị hợp lệ: Simple, Medium, Complex."
            )

        top_k = self.TOP_K_BY_COMPLEXITY[
            normalized_complexity
        ]

        return RetrievalBudget(
            complexity=normalized_complexity,
            top_k=top_k,
        )

    def get_top_k(
        self,
        complexity: str,
    ) -> int:
        """
        Trả trực tiếp retrieval top_k.
        """

        return self.get_budget(complexity).top_k

    def retrieve(
        self,
        query: str,
        final_top_k: int = FINAL_TOP_K,
    ) -> AdaptiveRetrievalResult:
        """
        Chạy toàn bộ adaptive retrieval pipeline.

        Args:
            query:
                Câu hỏi của người dùng.

            final_top_k:
                Số lượng chunks cuối cùng sau reranking.

        Returns:
            AdaptiveRetrievalResult chứa:

            - complexity:
                Kết quả phân loại query complexity.

            - budget:
                Retrieval top_k được adaptive lựa chọn.

            - candidates:
                Candidate pool sau Hybrid RRF.

            - results:
                Final chunks sau Cross-Encoder reranking
                và subject-aware adjustment.
        """

        if not query or not query.strip():
            raise ValueError(
                "Query không được để trống."
            )

        if final_top_k <= 0:
            raise ValueError(
                "final_top_k phải lớn hơn 0."
            )

        # --------------------------------------------------
        # 1. Query Complexity Classification
        # --------------------------------------------------

        complexity_result = self.classifier.classify(
            query
        )

        # --------------------------------------------------
        # 2. Adaptive Retrieval Budget
        # --------------------------------------------------

        budget = self.get_budget(
            complexity_result.level
        )

        # --------------------------------------------------
        # 3. Dense Retrieval
        # --------------------------------------------------

        dense_results = self.dense.retrieve(
            query,
            top_k=budget.top_k,
        )

        # --------------------------------------------------
        # 4. Sparse Retrieval - BM25
        # --------------------------------------------------

        bm25_results = self.bm25.retrieve(
            query,
            top_k=budget.top_k,
        )

        # --------------------------------------------------
        # 5. Hybrid Retrieval - RRF
        # --------------------------------------------------

        hybrid_results = self.hybrid.fuse(
            [dense_results, bm25_results],
            top_k=budget.top_k,
        )

        # --------------------------------------------------
        # 6. Cross-Encoder Reranking
        # --------------------------------------------------

        rerank_top_k = min(
            final_top_k,
            len(hybrid_results),
        )

        reranked_results = self.reranker.rerank(
            query,
            hybrid_results,
            top_k=rerank_top_k,
        )

        # --------------------------------------------------
        # 7. Subject-aware Adjustment
        # --------------------------------------------------

        reranked_results = _apply_subject_boost(
            query,
            reranked_results,
        )

        # --------------------------------------------------
        # 8. Return Complete Retrieval Result
        # --------------------------------------------------

        return AdaptiveRetrievalResult(
            complexity=complexity_result,
            budget=budget,
            candidates=hybrid_results,
            results=reranked_results,
        )