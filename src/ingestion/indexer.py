
from sqlalchemy.orm import Session

from src.db.models import Chunk, Document


class VectorIndexer:
    def __init__(self, db_session: Session):
        self.db = db_session

    def upsert_document(self, doc_metadata: dict) -> None:
        """Insert or update a legal document."""
        document = (
            self.db.query(Document)
            .filter(
                Document.document_id == doc_metadata["document_id"]
            )
            .first()
        )

        if document is None:
            document = Document(
                document_id=doc_metadata["document_id"],
                title=doc_metadata["title"],
                document_type=doc_metadata["document_type"],
                year=doc_metadata.get("year"),
                source=doc_metadata.get("source"),
                effective_date=doc_metadata.get("effective_date"),
                status=doc_metadata.get("status", "effective"),
            )
            self.db.add(document)
        else:
            document.title = doc_metadata["title"]
            document.document_type = doc_metadata["document_type"]
            document.year = doc_metadata.get("year")
            document.source = doc_metadata.get("source")
            document.effective_date = doc_metadata.get(
                "effective_date"
            )
            document.status = doc_metadata.get(
                "status",
                "effective",
            )

        self.db.commit()

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        """Insert or update chunks together with embeddings."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                "Số lượng chunks và embeddings không khớp."
            )

        for chunk, embedding in zip(chunks, embeddings):
            existing_chunk = (
                self.db.query(Chunk)
                .filter(
                    Chunk.document_id == chunk.document_id,
                    Chunk.chunk_index == chunk.chunk_index,
                )
                .first()
            )

            if existing_chunk is None:
                chunk.embedding = embedding
                self.db.add(chunk)
            else:
                existing_chunk.article_title = chunk.article_title
                existing_chunk.chunk_type = chunk.chunk_type
                existing_chunk.content = chunk.content
                existing_chunk.embedding = embedding
                existing_chunk.chunk_metadata = chunk.chunk_metadata

        self.db.commit()