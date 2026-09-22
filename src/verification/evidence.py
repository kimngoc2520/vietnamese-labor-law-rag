import re


def _normalize(text: str) -> str:
    """Normalize text for simple evidence matching."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_answer_sentences(answer: str) -> list[str]:
    """Split answer into simple factual units."""
    sentences = re.split(r"[.!?;]\s+|\n+", answer)
    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def _keyword_coverage(
    sentence: str,
    evidence_text: str,
) -> float:
    """Calculate keyword coverage between a claim and one evidence chunk."""
    sentence = _normalize(sentence)
    evidence_text = _normalize(evidence_text)

    words = re.findall(r"\b\w+\b", sentence)

    keywords = [
        word
        for word in words
        if len(word) >= 4
    ]

    if not keywords:
        return 0.0

    matched = sum(
        1
        for keyword in keywords
        if keyword in evidence_text
    )

    return matched / len(keywords)


def _supported_by_evidence(
    sentence: str,
    evidence_text: str,
) -> bool:
    """Check whether the important terms in a sentence appear in evidence."""
    return _keyword_coverage(sentence, evidence_text) >= 0.6


def select_evidence(
    answer: str,
    evidence: list[dict],
    threshold: float = 0.6,
) -> list[dict]:
    """Select the strongest evidence chunk for each answer claim."""

    if not answer.strip() or not evidence:
        return []

    sentences = _extract_answer_sentences(answer)

    if not sentences:
        return []

    selected_chunks = []

    for sentence in sentences:
        normalized_sentence = _normalize(sentence)

        article_match_result = re.search(
            r"\bđiều\s+(\d+)\b",
            normalized_sentence,
        )

        article_number = (
            article_match_result.group(1)
            if article_match_result
            else None
        )

        candidates = []

        for chunk in evidence:
            content = chunk.get("content", "").strip()
            article_title = _normalize(
                chunk.get("article_title", "")
            )

            if not content:
                continue

            coverage = _keyword_coverage(
                sentence,
                content,
            )

            if coverage < threshold:
                continue

            # If the answer explicitly mentions an article,
            # only consider chunks from that article.
            if article_number:
                article_match = bool(
                    re.search(
                        rf"\bđiều\s+{article_number}\b",
                        article_title,
                    )
                )

                if not article_match:
                    continue

            candidates.append((coverage, chunk))

        if candidates:
            best_chunk = max(
                candidates,
                key=lambda item: item[0],
            )[1]

            if best_chunk not in selected_chunks:
                selected_chunks.append(best_chunk)

    return selected_chunks

def verify_answer(
    answer: str,
    evidence: list[dict],
) -> bool:
    """Verify whether the answer has sufficient textual support."""
    if not answer.strip() or not evidence:
        return False

    evidence_text = "\n".join(
        chunk.get("content", "")
        for chunk in evidence
        if chunk.get("content")
    )

    if not evidence_text:
        return False

    sentences = _extract_answer_sentences(answer)

    if not sentences:
        return False

    supported = sum(
        1
        for sentence in sentences
        if _supported_by_evidence(sentence, evidence_text)
    )

    support_ratio = supported / len(sentences)

    return support_ratio >= 0.6