def extract_claims(answer: str) -> list[str]:
    return [claim.strip() for claim in answer.split(".") if claim.strip()]
