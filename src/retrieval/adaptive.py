from dataclasses import dataclass
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.retrieval.complexity import (
    ComplexityResult,
    QueryComplexityClassifier,
)
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.sparse import BM25Retriever


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
    candidates: List[Dict[str, Any]]
    results: List[Dict[str, Any]]


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
        Final Results

    MVP policy:

        Simple   → top_k = 5
        Medium   → top_k = 10
        Complex  → top_k = 20
    """

    TOP_K_BY_COMPLEXITY = {
        "Simple": 5,
        "Medium": 10,
        "Complex": 20,
    }

    FINAL_TOP_K = 5

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
                Final chunks sau Cross-Encoder reranking.
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
        # 7. Return Complete Retrieval Result
        # --------------------------------------------------

        return AdaptiveRetrievalResult(
            complexity=complexity_result,
            budget=budget,
            candidates=hybrid_results,
            results=reranked_results,
        )