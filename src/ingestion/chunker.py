import re
from typing import Any, Dict, List

from src.db.models import Chunk


class VietnameseLegalChunker:
    """
    Chunk Vietnamese legal documents using a structure-aware strategy.

    Strategy:
    1. Split the document by legal Articles (Điều).
    2. Keep each Article as one chunk when it fits the size limit.
    3. Split long Articles using clauses / paragraphs.
    4. Preserve the Article heading in every sub-chunk.
    5. Add a small overlap between sub-chunks when possible.
    """

    def __init__(
        self,
        max_chars: int = 3000,
        min_chars: int = 300,
        overlap_chars: int = 300,
    ):
        self.max_chars = max_chars
        self.min_chars = min_chars
        self.overlap_chars = overlap_chars

        # Example:
        # Điều 1. Phạm vi điều chỉnh.
        # Điều 2. Đối tượng áp dụng
        self.article_pattern = re.compile(
            r"(?m)^\s*(Điều\s+\d+\.\s*[^\n]*)"
        )

        # Example:
        # 1. Người lao động...
        # 2. Người sử dụng lao động...
        self.clause_pattern = re.compile(
            r"(?m)^\s*(\d+\.\s+)"
        )

    def _split_articles(
        self,
        text: str,
    ) -> List[tuple[str, str]]:
        """
        Split document into:
        [(article_title, article_content), ...]
        """
        matches = list(
            self.article_pattern.finditer(text)
        )

        if not matches:
            return [
                ("Mở đầu / Phần chung", text.strip())
            ]

        sections = []

        # Text before the first Article.
        prefix = text[: matches[0].start()].strip()

        if prefix:
            sections.append(
                ("Mở đầu / Phần chung", prefix)
            )

        for index, match in enumerate(matches):
            article_title = match.group(1).strip()

            content_start = match.end()

            if index + 1 < len(matches):
                content_end = matches[index + 1].start()
            else:
                content_end = len(text)

            content = text[
                content_start:content_end
            ].strip()

            sections.append(
                (article_title, content)
            )

        return sections

    def _split_long_article(
        self,
        article_title: str,
        content: str,
    ) -> List[str]:
        """
        Split a long Article into smaller chunks.

        Prefer clause boundaries, then paragraph
        boundaries, then hard splitting.
        """
        full_text = (
            f"{article_title}\n{content}"
        ).strip()

        if len(full_text) <= self.max_chars:
            return [full_text]

        # First try splitting by legal clauses.
        clauses = self._split_by_pattern(
            content,
            self.clause_pattern,
        )

        if len(clauses) > 1:
            return self._pack_units(
                article_title,
                clauses,
            )

        # If there are no useful clauses,
        # try paragraph boundaries.
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(
                r"\n\s*\n",
                content,
            )
            if paragraph.strip()
        ]

        if len(paragraphs) > 1:
            return self._pack_units(
                article_title,
                paragraphs,
            )

        # Final fallback.
        return self._hard_split(
            article_title,
            content,
        )

    @staticmethod
    def _split_by_pattern(
        text: str,
        pattern: re.Pattern,
    ) -> List[str]:
        """
        Split text while keeping the matched marker
        such as '1.' with its content.
        """
        matches = list(
            pattern.finditer(text)
        )

        if not matches:
            return (
                [text.strip()]
                if text.strip()
                else []
            )

        units = []

        # Text before the first matched unit.
        prefix = text[: matches[0].start()].strip()

        if prefix:
            units.append(prefix)

        for index, match in enumerate(matches):
            start = match.start()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(text)

            unit = text[start:end].strip()

            if unit:
                units.append(unit)

        return units

    def _pack_units(
        self,
        article_title: str,
        units: List[str],
    ) -> List[str]:
        """
        Pack legal units into chunks without exceeding
        max_chars.

        Overlap is used only when the resulting chunk
        still satisfies max_chars.
        """
        chunks = []
        current_units = []

        for unit in units:
            candidate_units = (
                current_units + [unit]
            )

            candidate = self._build_chunk_text(
                article_title,
                candidate_units,
            )

            if (
                current_units
                and len(candidate) > self.max_chars
            ):
                # Save the current chunk first.
                chunks.append(
                    self._build_chunk_text(
                        article_title,
                        current_units,
                    )
                )

                # Try to preserve a small overlap.
                overlap = self._make_overlap(
                    current_units
                )

                candidate_with_overlap = (
                    self._build_chunk_text(
                        article_title,
                        overlap + [unit],
                    )
                )

                if (
                    len(candidate_with_overlap)
                    <= self.max_chars
                ):
                    current_units = (
                        overlap + [unit]
                    )
                else:
                    # Hard size limit takes priority
                    # over overlap.
                    current_units = [unit]

            else:
                current_units = candidate_units

        if current_units:
            chunks.append(
                self._build_chunk_text(
                    article_title,
                    current_units,
                )
            )

        return chunks

    @staticmethod
    def _build_chunk_text(
        article_title: str,
        units: List[str],
    ) -> str:
        """
        Build final chunk text while preserving
        the Article heading.
        """
        return (
            f"{article_title}\n"
            + "\n\n".join(units)
        )

    def _make_overlap(
        self,
        units: List[str],
    ) -> List[str]:
        """
        Keep a small portion of the last legal unit
        as overlap when possible.
        """
        if not units:
            return []

        last_unit = units[-1]

        if len(last_unit) <= self.overlap_chars:
            return [last_unit]

        return [
            last_unit[-self.overlap_chars:]
        ]

    def _hard_split(
        self,
        article_title: str,
        content: str,
    ) -> List[str]:
        """
        Final fallback for unusually long text
        without recognizable legal boundaries.

        Every generated chunk respects max_chars.
        """
        chunks = []

        available_chars = (
            self.max_chars
            - len(article_title)
            - 1
        )

        if available_chars <= 0:
            raise ValueError(
                "max_chars is too small for the "
                "Article title."
            )

        start = 0

        while start < len(content):
            end = min(
                start + available_chars,
                len(content),
            )

            piece = content[
                start:end
            ].strip()

            if piece:
                chunks.append(
                    f"{article_title}\n{piece}"
                )

            if end >= len(content):
                break

            start = max(
                end - self.overlap_chars,
                start + 1,
            )

        return chunks

    def split(
        self,
        text: str,
        doc_metadata: Dict[str, Any],
    ) -> List[Chunk]:
        """
        Convert a legal document into SQLAlchemy
        Chunk objects.
        """
        text = text.strip()

        if not text:
            return []

        articles = self._split_articles(text)

        chunks = []
        chunk_index = 0

        for article_title, content in articles:
            if not content:
                continue

            article_chunks = (
                self._split_long_article(
                    article_title,
                    content,
                )
            )

            for chunk_text in article_chunks:
                if (
                    len(chunk_text.strip())
                    < self.min_chars
                ):
                    continue

                chunk_metadata = {
                    "document_id": (
                        doc_metadata["document_id"]
                    ),
                    "document_title": (
                        doc_metadata["title"]
                    ),
                    "article": article_title,
                    "chunk_index": chunk_index,
                }

                chunks.append(
                    Chunk(
                        document_id=(
                            doc_metadata["document_id"]
                        ),
                        chunk_index=chunk_index,
                        article_title=article_title,
                        chunk_type="article_content",
                        content=chunk_text,
                        chunk_metadata=chunk_metadata,
                    )
                )

                chunk_index += 1

        return chunks