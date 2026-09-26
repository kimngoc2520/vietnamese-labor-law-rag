from typing import Any

from rank_bm25 import BM25Okapi
from sqlalchemy import text
from sqlalchemy.orm import Session


class BM25Retriever:
    """
    Sparse retrieval sử dụng BM25 (Okapi).

    Toàn bộ chunks được load từ PostgreSQL vào memory
    để xây dựng BM25 index.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

        self.corpus: list[dict[str, Any]] = []
        self.tokenized_corpus: list[list[str]] = []

        self.bm25: BM25Okapi | None = None

        self._load_corpus()

    def _load_corpus(self) -> None:
        """
        Load toàn bộ chunks từ database
        và xây dựng BM25 index.
        """

        print("Đang load corpus cho BM25...")

        result = self.db.execute(
            text(
                """
                SELECT
                    document_id,
                    chunk_index,
                    article_title,
                    content,
                    metadata
                FROM chunks
                """
            )
        )

        self.corpus = []

        for row in result:
            self.corpus.append(
                {
                    "document_id": row.document_id,
                    "chunk_index": row.chunk_index,
                    "article_title": row.article_title,
                    "content": row.content,
                    "metadata": row.metadata,
                }
            )

        # Tokenization MVP:
        # lowercase + whitespace split.
        self.tokenized_corpus = [
            document["content"].lower().split()
            for document in self.corpus
        ]

        self.bm25 = BM25Okapi(
            self.tokenized_corpus
        )

        print(
            "BM25 index sẵn sàng với "
            f"{len(self.corpus)} chunks"
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Retrieve top-k chunks bằng BM25.
        """

        if self.bm25 is None:
            raise RuntimeError(
                "BM25 index chưa được khởi tạo."
            )

        tokenized_query = (
            query.lower().split()
        )

        scores = self.bm25.get_scores(
            tokenized_query
        )

        top_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )[:top_k]

        results = []

        for index in top_indices:
            document = self.corpus[index].copy()

            document["score"] = float(
                scores[index]
            )

            results.append(document)

        return results