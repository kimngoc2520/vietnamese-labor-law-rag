def build_citation(chunk: dict) -> str:
    """Build a user-facing legal citation from a retrieved chunk."""

    article_title = chunk.get("article_title", "").strip()
    document_id = chunk.get("document_id", "").strip()

    if not article_title or not document_id:
        return ""

    document_names = {
        "BLLD_2019": "Bộ luật Lao động 2019",
        "ND_145_2020": "Nghị định 145/2020/NĐ-CP",
        "ND_12_2022": "Nghị định 12/2022/NĐ-CP",
        "TT_10_2020": "Thông tư 10/2020/TT-BLĐTBXH",
        "AL_70_2023": "Án lệ 70/2023/AL",
    }

    document_name = document_names.get(document_id, document_id)

    return f"{article_title}, {document_name}"


def build_citations(chunks: list[dict]) -> list[str]:
    """Build unique user-facing citations from retrieved chunks."""

    citations = []

    for chunk in chunks:
        citation = build_citation(chunk)

        if citation and citation not in citations:
            citations.append(citation)

    return citations