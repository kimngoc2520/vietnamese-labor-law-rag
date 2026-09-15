from src.verification.evidence import verify_answer


def test_evidence_requires_answer_and_evidence() -> None:
    assert verify_answer("answer", ["evidence"])
    assert not verify_answer("", ["evidence"])
