import json
import os
import sys
from pathlib import Path

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from src.db.connection import SessionLocal
from src.ingestion.pipeline import IngestionPipeline


DATA_DIR = Path("data/raw")
METADATA_FILE = DATA_DIR / "metadata.json"


def main() -> None:
    print("Bắt đầu ingestion pipeline...")

    with METADATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata_config = json.load(file)

    documents = metadata_config["documents"]

    db = SessionLocal()

    try:
        pipeline = IngestionPipeline(db)

        total_chunks = 0

        for metadata in documents:
            filename = metadata["filename"]
            pdf_path = DATA_DIR / filename

            if not pdf_path.exists():
                print(
                    f"Bỏ qua: {filename} "
                    "(không tìm thấy file)"
                )
                continue

            try:
                chunk_count = pipeline.process_file(
                    pdf_path,
                    fallback_metadata=metadata,
                )

                total_chunks += chunk_count

            except Exception as exc:
                db.rollback()

                print(
                    f"Lỗi khi xử lý {filename}: {exc}"
                )

        print(
            f"\n Ingestion hoàn tất. "
            f"Tổng chunks xử lý: {total_chunks}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()