from src.agent.router import route


def test_router_defaults_to_rag() -> None:
    assert route("question") == "rag"
