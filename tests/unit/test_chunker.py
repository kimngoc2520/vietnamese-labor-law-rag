from src.ingestion.chunker import VietnameseLegalChunker


def make_metadata():
    return {
        "document_id": "TEST-001",
        "title": "Bộ luật Lao động thử nghiệm",
    }


def test_split_articles():
    text = """
Điều 1. Phạm vi điều chỉnh.
Bộ luật này quy định tiêu chuẩn lao động.

Điều 2. Đối tượng áp dụng.
Người lao động và người sử dụng lao động.
"""

    chunker = VietnameseLegalChunker(
        min_chars=1,
        max_chars=3000,
    )

    chunks = chunker.split(text, make_metadata())

    assert len(chunks) == 2

    assert chunks[0].article_title == "Điều 1. Phạm vi điều chỉnh."
    assert chunks[1].article_title == "Điều 2. Đối tượng áp dụng."

    assert "Bộ luật này quy định" in chunks[0].content
    assert "Người lao động" in chunks[1].content


def test_preserve_metadata():
    text = """
Điều 1. Phạm vi điều chỉnh.
Nội dung của điều.
"""

    chunker = VietnameseLegalChunker(
        min_chars=1,
    )

    chunks = chunker.split(text, make_metadata())

    chunk = chunks[0]

    assert chunk.document_id == "TEST-001"
    assert chunk.article_title == "Điều 1. Phạm vi điều chỉnh."

    assert chunk.chunk_metadata["document_id"] == "TEST-001"
    assert (
        chunk.chunk_metadata["document_title"]
        == "Bộ luật Lao động thử nghiệm"
    )


def test_long_article_is_split():
    clauses = "\n\n".join(
        [
            f"{i}. " + ("Nội dung quy định của khoản. " * 30)
            for i in range(1, 8)
        ]
    )

    text = f"""
Điều 3. Quy định chi tiết.
{clauses}
"""

    chunker = VietnameseLegalChunker(
        max_chars=1000,
        min_chars=1,
        overlap_chars=100,
    )

    chunks = chunker.split(text, make_metadata())

    assert len(chunks) > 1

    for chunk in chunks:
        assert len(chunk.content) <= 1000
        assert "Điều 3. Quy định chi tiết." in chunk.content


def test_article_heading_preserved_in_every_subchunk():
    clauses = "\n\n".join(
        [
            f"{i}. " + ("Quy định về người lao động. " * 50)
            for i in range(1, 6)
        ]
    )

    text = f"""
Điều 5. Quyền và nghĩa vụ.
{clauses}
"""

    chunker = VietnameseLegalChunker(
        max_chars=800,
        min_chars=1,
        overlap_chars=100,
    )

    chunks = chunker.split(text, make_metadata())

    assert len(chunks) > 1

    for chunk in chunks:
        assert (
            chunk.article_title
            == "Điều 5. Quyền và nghĩa vụ."
        )
        assert chunk.content.startswith(
            "Điều 5. Quyền và nghĩa vụ."
        )


def test_empty_text():
    chunker = VietnameseLegalChunker()

    assert chunker.split("", make_metadata()) == []