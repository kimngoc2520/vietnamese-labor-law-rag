import re


CALCULATOR_PATTERNS = [
    r"\d+\s*[\+\-\*/]\s*\d+",
    r"\d+\s*(%|phần trăm)",
    r"\b(tính|tổng|hiệu|nhân|chia)\b",
]

WEB_SEARCH_PATTERNS = [
    r"\b(mới nhất|hiện tại|hôm nay|2026|cập nhật)\b",
    r"\b(tìm kiếm|tra cứu trên mạng|internet|web)\b",
]


def route(query: str) -> str:
    """Classify a user query into an execution route."""
    normalized = query.strip().lower()

    if any(re.search(pattern, normalized) for pattern in CALCULATOR_PATTERNS):
        return "calculator"

    if any(re.search(pattern, normalized) for pattern in WEB_SEARCH_PATTERNS):
        return "web_search"

    return "rag"