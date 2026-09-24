from src.verification.evidence import (
    select_evidence,
    verify_answer,
)


def test_verify_answer_requires_answer_and_evidence() -> None:
    evidence = [{"content": "Người lao động có quyền đơn phương chấm dứt hợp đồng."}]

    assert verify_answer("Người lao động có quyền đơn phương chấm dứt hợp đồng.", evidence)
    assert not verify_answer("", evidence)
    assert not verify_answer("answer", [])


def test_select_evidence_matches_article_number() -> None:
    evidence = [
        {
            "content": "Người lao động có quyền đơn phương chấm dứt hợp đồng.",
            "article_title": "Điều 35. Quyền đơn phương chấm dứt hợp đồng của người lao động",
        },
        {
            "content": "Người sử dụng lao động có quyền đơn phương chấm dứt hợp đồng.",
            "article_title": "Điều 36. Quyền đơn phương chấm dứt hợp đồng của người sử dụng lao động",
        },
    ]

    answer = "Theo Điều 35, người lao động có quyền đơn phương chấm dứt hợp đồng."

    selected = select_evidence(answer, evidence)

    assert len(selected) == 1
    assert selected[0]["article_title"].startswith("Điều 35")


def test_select_evidence_rejects_wrong_article() -> None:
    evidence = [
        {
            "content": "Người sử dụng lao động có quyền đơn phương chấm dứt hợp đồng.",
            "article_title": "Điều 36. Quyền đơn phương chấm dứt hợp đồng của người sử dụng lao động",
        },
    ]

    answer = "Theo Điều 35, người lao động có quyền đơn phương chấm dứt hợp đồng."

    selected = select_evidence(answer, evidence)

    assert selected == []


def test_select_evidence_returns_empty_for_empty_input() -> None:
    assert select_evidence("", []) == []
    assert select_evidence("Some answer", []) == []