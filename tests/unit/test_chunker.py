from src.ingestion.chunker import chunk_text


def test_chunk_text_splits_input() -> None:
    assert chunk_text("abcdef", chunk_size=2) == ["ab", "cd", "ef"]
