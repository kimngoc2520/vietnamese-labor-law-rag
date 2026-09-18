from dataclasses import dataclass
import re


@dataclass
class ComplexityResult:
    """
    Kết quả phân loại độ phức tạp của query.
    """

    level: str
    score: float
    reasons: list[str]


class QueryComplexityClassifier:
    """
    Phân loại query thành Simple / Medium / Complex.

    MVP sử dụng các đặc trưng có thể giải thích được:
    - Độ dài query
    - Số lượng câu hỏi / mệnh đề
    - Từ khóa thể hiện điều kiện hoặc quan hệ
    - Số lượng phạm vi pháp lý được đề cập

    Đây là baseline rule-based, chưa phải ML classifier.
    """

    SIMPLE_THRESHOLD = 2.0
    COMPLEX_THRESHOLD = 4.0

    CONDITION_KEYWORDS = {
        "nếu",
        "khi",
        "trong trường hợp",
        "trừ khi",
        "ngoại trừ",
        "điều kiện",
        "đối với",
        "trường hợp",
    }

    RELATION_KEYWORDS = {
        "và",
        "hoặc",
        "đồng thời",
        "kết hợp",
        "so với",
        "khác với",
        "cũng như",
    }

    LEGAL_SCOPE_KEYWORDS = {
        "người lao động",
        "người sử dụng lao động",
        "hợp đồng lao động",
        "tiền lương",
        "bảo hiểm xã hội",
        "thời giờ làm việc",
        "thời giờ nghỉ ngơi",
        "kỷ luật lao động",
        "trợ cấp",
        "chế độ",
    }

    def classify(self, query: str) -> ComplexityResult:
        """
        Phân loại độ phức tạp của một query.

        Returns:
            ComplexityResult:
                level: Simple / Medium / Complex
                score: điểm complexity
                reasons: các lý do dẫn đến classification
        """

        if not query or not query.strip():
            raise ValueError(
                "Query không được để trống."
            )

        normalized_query = self._normalize(query)

        score = 0.0
        reasons: list[str] = []

        # ==================================================
        # 1. Query length
        # ==================================================

        word_count = len(
            normalized_query.split()
        )

        if word_count >= 30:
            score += 2.0
            reasons.append(
                "query dài"
            )
        elif word_count >= 15:
            score += 1.0
            reasons.append(
                "query có độ dài trung bình"
            )

        # ==================================================
        # 2. Number of question clauses
        # ==================================================

        question_count = self._count_questions(
            normalized_query
        )

        if question_count >= 2:
            score += 2.0
            reasons.append(
                "có nhiều câu hỏi"
            )

        # ==================================================
        # 3. Conditional / legal conditions
        # ==================================================

        condition_matches = self._count_keywords(
            normalized_query,
            self.CONDITION_KEYWORDS,
        )

        if condition_matches >= 2:
            score += 2.0
            reasons.append(
                "có nhiều điều kiện pháp lý"
            )
        elif condition_matches == 1:
            score += 1.0
            reasons.append(
                "có điều kiện pháp lý"
            )

        # ==================================================
        # 4. Multiple relations / requirements
        # ==================================================

        relation_matches = self._count_keywords(
            normalized_query,
            self.RELATION_KEYWORDS,
        )

        if relation_matches >= 2:
            score += 1.5
            reasons.append(
                "có nhiều quan hệ hoặc thành phần"
            )
        elif relation_matches == 1:
            score += 0.5
            reasons.append(
                "có nhiều thành phần trong query"
            )

        # ==================================================
        # 5. Number of legal scopes
        # ==================================================

        scope_matches = self._count_keywords(
            normalized_query,
            self.LEGAL_SCOPE_KEYWORDS,
        )

        if scope_matches >= 3:
            score += 2.0
            reasons.append(
                "liên quan nhiều phạm vi pháp lý"
            )
        elif scope_matches >= 2:
            score += 1.0
            reasons.append(
                "liên quan nhiều hơn một phạm vi pháp lý"
            )

        # ==================================================
        # 6. Classify
        # ==================================================

        if score < self.SIMPLE_THRESHOLD:
            level = "Simple"
        elif score < self.COMPLEX_THRESHOLD:
            level = "Medium"
        else:
            level = "Complex"

        if not reasons:
            reasons.append(
                "query có cấu trúc đơn giản"
            )

        return ComplexityResult(
            level=level,
            score=score,
            reasons=reasons,
        )

    @staticmethod
    def _normalize(query: str) -> str:
        """
        Chuẩn hóa query trước khi phân tích.
        """

        query = query.lower().strip()

        query = re.sub(
            r"\s+",
            " ",
            query,
        )

        return query

    @staticmethod
    def _count_questions(query: str) -> int:
        """
        Đếm số dấu hỏi trong query.
        """

        return query.count("?")

    @staticmethod
    def _count_keywords(
        query: str,
        keywords: set[str],
    ) -> int:
        """
        Đếm số keyword/phrase xuất hiện trong query.

        Mỗi keyword được tính tối đa một lần.
        """

        count = 0

        for keyword in keywords:
            if keyword in query:
                count += 1

        return count


if __name__ == "__main__":
    classifier = QueryComplexityClassifier()

    test_queries = [
        "Thời gian thử việc tối đa là bao lâu?",
        (
            "Người lao động đơn phương chấm dứt hợp đồng "
            "lao động phải báo trước bao nhiêu ngày?"
        ),
        (
            "Nếu người lao động đơn phương chấm dứt hợp đồng "
            "lao động khi người sử dụng lao động vi phạm nghĩa vụ "
            "thì có phải báo trước không và có được hưởng trợ cấp "
            "thôi việc hay không?"
        ),
    ]

    for query in test_queries:
        result = classifier.classify(query)

        print("=" * 60)
        print(f"Query: {query}")
        print(f"Level: {result.level}")
        print(f"Score: {result.score}")
        print("Reasons:")

        for reason in result.reasons:
            print(f"  - {reason}")