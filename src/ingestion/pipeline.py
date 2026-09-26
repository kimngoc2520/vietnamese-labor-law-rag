from pathlib import Path

from sqlalchemy.orm import Session

from src.ingestion.chunker import VietnameseLegalChunker
from src.ingestion.cleaner import TextCleaner
from src.ingestion.embedder import LegalEmbedder
from src.ingestion.indexer import VectorIndexer
from src.ingestion.loader import DocumentLoader


class IngestionPipeline:
    def __init__(self, db_session: Session):
        self.loader = DocumentLoader()
        self.cleaner = TextCleaner()
        self.chunker = VietnameseLegalChunker()
        self.embedder = LegalEmbedder()
        self.indexer = VectorIndexer(db_session)

    def process_file(
        self,
        file_path: Path,
        fallback_metadata: dict | None = None,
    ) -> int:
        print(f" Đang xử lý: {file_path.name}")

        # 1. Load
        raw_text, file_metadata = self.loader.load(file_path)

        metadata = {
            **(fallback_metadata or {}),
            **(file_metadata or {}),
        }

        if not metadata.get("document_id"):
            raise ValueError(
                f"Thiếu document_id cho file {file_path.name}"
            )

        # 2. Clean
        clean_text = self.cleaner.clean(raw_text)

        if not clean_text:
            raise ValueError(
                f"Không trích xuất được nội dung từ {file_path.name}"
            )

        # 3. Chunk
        chunks = self.chunker.split(
            clean_text,
            metadata,
        )

        print(f"   -> Tạo được {len(chunks)} chunks")

        if not chunks:
            print(
                "   Không có chunk nào được tạo, bỏ qua."
            )
            return 0

        # 4. Embed
        texts_to_embed = [
            chunk.content
            for chunk in chunks
        ]

        embeddings = self.embedder.embed(
            texts_to_embed
        )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Số lượng embeddings không khớp với số lượng chunks."
            )

        # 5. Index
        self.indexer.upsert_document(metadata)
        self.indexer.upsert_chunks(
            chunks,
            embeddings,
        )

        print(
            f"   Đã lưu {len(chunks)} chunks vào database"
        )

        return len(chunks)