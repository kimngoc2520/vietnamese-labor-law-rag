from src.agent.router import route


def test_router_defaults_to_rag() -> None:
    assert route("question") == "rag"


def test_router_detects_calculator_expression() -> None:
    assert route("25 + 17 bằng bao nhiêu?") == "calculator"


def test_router_detects_percentage_calculation() -> None:
    assert route("Tính 20 phần trăm của 500") == "calculator"


def test_router_detects_calculator_keywords() -> None:
    assert route("Tính tổng tiền lương") == "calculator"


def test_router_detects_web_search_for_latest_information() -> None:
    assert route("Thông tin mới nhất về luật lao động") == "web_search"


def test_router_detects_web_search_for_current_information() -> None:
    assert route("Quy định hiện tại về lao động") == "web_search"


def test_router_detects_web_search_for_explicit_web_request() -> None:
    assert route("Tìm kiếm trên web về luật lao động") == "web_search"


def test_router_strips_whitespace_and_normalizes_case() -> None:
    assert route("   QUESTION   ") == "rag"