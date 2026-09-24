import pytest

from src.retrieval.complexity import QueryComplexityClassifier


@pytest.fixture
def classifier() -> QueryComplexityClassifier:
    return QueryComplexityClassifier()


def test_empty_query_raises_value_error(
    classifier: QueryComplexityClassifier,
) -> None:
    with pytest.raises(ValueError, match="Query không được để trống"):
        classifier.classify("")


def test_whitespace_query_raises_value_error(
    classifier: QueryComplexityClassifier,
) -> None:
    with pytest.raises(ValueError, match="Query không được để trống"):
        classifier.classify("   ")


def test_simple_query(
    classifier: QueryComplexityClassifier,
) -> None:
    result = classifier.classify(
        "Thời gian thử việc tối đa là bao lâu?"
    )

    assert result.level == "Simple"
    assert result.score == 0.0
    assert result.reasons == ["query có cấu trúc đơn giản"]


def test_medium_query_from_length(
    classifier: QueryComplexityClassifier,
) -> None:
    query = (
        "Người lao động có quyền đơn phương chấm dứt hợp đồng "
        "lao động trong những trường hợp nào theo quy định pháp luật hiện hành?"
    )

    result = classifier.classify(query)

    assert result.level == "Medium"
    assert result.score == 3.0
    assert "query có độ dài trung bình" in result.reasons
    assert "có điều kiện pháp lý" in result.reasons
    assert "liên quan nhiều hơn một phạm vi pháp lý" in result.reasons


def test_long_query_adds_two_points(
    classifier: QueryComplexityClassifier,
) -> None:
    query = " ".join(["lao động"] * 30)

    result = classifier.classify(query)

    assert result.score == 2.0
    assert result.level == "Medium"
    assert "query dài" in result.reasons


def test_multiple_questions_add_two_points(
    classifier: QueryComplexityClassifier,
) -> None:
    query = (
        "Người lao động có được nghỉ phép không? "
        "Người sử dụng lao động có được từ chối không?"
    )

    result = classifier.classify(query)

    assert result.score == 4.0
    assert result.level == "Complex"
    assert "query có độ dài trung bình" in result.reasons
    assert "có nhiều câu hỏi" in result.reasons
    assert "liên quan nhiều hơn một phạm vi pháp lý" in result.reasons


def test_legal_condition_adds_one_point(
    classifier: QueryComplexityClassifier,
) -> None:
    query = (
        "Nếu người lao động nghỉ việc thì có được hưởng trợ cấp không?"
    )

    result = classifier.classify(query)

    assert result.score == 2.0
    assert result.level == "Medium"
    assert "có điều kiện pháp lý" in result.reasons
    assert "liên quan nhiều hơn một phạm vi pháp lý" in result.reasons


def test_multiple_relations_and_legal_scopes_make_query_complex(
    classifier: QueryComplexityClassifier,
) -> None:
    query = (
        "Nếu người lao động và người sử dụng lao động đồng thời có "
        "tranh chấp về hợp đồng lao động, tiền lương, bảo hiểm xã hội "
        "và thời giờ làm việc thì quyền và nghĩa vụ của mỗi bên "
        "được xác định như thế nào?"
    )

    result = classifier.classify(query)

    assert result.level == "Complex"
    assert result.score >= 4.0
    assert "có điều kiện pháp lý" in result.reasons
    assert "có nhiều quan hệ hoặc thành phần" in result.reasons
    assert "liên quan nhiều phạm vi pháp lý" in result.reasons


def test_normalization_and_keyword_matching(
    classifier: QueryComplexityClassifier,
) -> None:
    query = (
        "  NẾU   người lao động   và   người sử dụng lao động "
        "có tranh chấp?  "
    )

    result = classifier.classify(query)

    assert result.score == 2.5
    assert result.level == "Medium"
    assert "có điều kiện pháp lý" in result.reasons
    assert "có nhiều thành phần trong query" in result.reasons
    assert "liên quan nhiều hơn một phạm vi pháp lý" in result.reasons