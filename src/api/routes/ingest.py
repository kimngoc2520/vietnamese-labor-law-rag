from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.api.schemas.ingest import IngestResponse
from src.db.connection import SessionLocal
from src.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/ingest", tags=["ingestion"])


ALLOWED_EXTENSIONS = {".pdf"}


@router.post("", response_model=IngestResponse)
def ingest_document(
    file: UploadFile = File(...),  # noqa: B008
) -> IngestResponse:
    filename = file.filename or "uploaded_document"

    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    db = SessionLocal()

    try:
        file_bytes = file.file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        with NamedTemporaryFile(
            suffix=suffix,
            delete=True,
        ) as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush()

            pipeline = IngestionPipeline(db)

            chunks_indexed = pipeline.process_file(
                Path(temp_file.name),
            )

        return IngestResponse(
            status="success",
            filename=filename,
            chunks_indexed=chunks_indexed,
        )

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {exc}",
        ) from exc

    finally:
        db.close()