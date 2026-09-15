from pathlib import Path

from .chunker import chunk_text
from .cleaner import clean_text
from .loader import load_text


def ingest_file(path: str | Path) -> list[str]:
    return chunk_text(clean_text(load_text(path)))
