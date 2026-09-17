from typing import List

from sqlalchemy.orm import Session

from src.db.models import Chunk, Document


class VectorIndexer:
    def __init__(self, db_session: Session):
        self.db = db_session

    def upsert_document(self, doc_metadata: dict) -> None:
        """Insert or update a legal document."""
        document = Document(
            document_id=doc_metadata["document_id"],
            title=doc_metadata["title"],
            document_type=doc_metadata["document_type"],
            year=doc_metadata.get("year"),
            source=doc_metadata.get("source"),
            effective_date=doc_metadata.get("effective_date"),
            status=doc_metadata.get("status", "effective"),
        )

        self.db.merge(document)
        self.db.commit()

    def upsert_chunks(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
    ) -> None:
        """Insert or update chunks together with embeddings."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                "Số lượng chunks và embeddings không khớp."
            )

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
            self.db.merge(chunk)

        self.db.commit()