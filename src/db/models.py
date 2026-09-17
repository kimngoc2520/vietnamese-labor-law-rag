from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector


Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(50), unique=True, index=True)
    title = Column(Text)
    document_type = Column(String(50))
    year = Column(Integer)
    source = Column(String(50))
    effective_date = Column(String(50))
    status = Column(String(50))


class Chunk(Base):
    __tablename__ = "chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_chunks_document_chunk_index",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        String(50),
        ForeignKey("documents.document_id"),
        index=True,
    )

    chunk_index = Column(Integer)
    article_title = Column(Text, nullable=True)
    chunk_type = Column(String(50))
    content = Column(Text)
    embedding = Column(Vector(1024))
    chunk_metadata = Column("metadata", JSON)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )