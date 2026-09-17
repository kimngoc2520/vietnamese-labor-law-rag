import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Tuple

import pymupdf
import pytesseract
import yaml
from PIL import Image
from pypdf import PdfReader


class DocumentLoader:
    OCR_MIN_CHARS = 100

    @staticmethod
    def _extract_pdf_text(file_path: Path) -> str:
        """Extract text from a text-based PDF using pypdf."""
        reader = PdfReader(file_path)

        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")

        return "\n".join(pages).strip()

    @staticmethod
    def _ocr_pdf(file_path: Path) -> str:
        """OCR a scanned PDF using Tesseract Vietnamese."""
        document = pymupdf.open(file_path)
        pages = []

        try:
            for page_number, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2)
                )

                image = Image.open(
                    BytesIO(pixmap.tobytes("png"))
                )

                text = pytesseract.image_to_string(
                    image,
                    lang="vie",
                    config="--psm 6",
                )

                if text.strip():
                    pages.append(
                        f"[Page {page_number}]\n{text.strip()}"
                    )

        finally:
            document.close()

        return "\n\n".join(pages).strip()

    @classmethod
    def load_pdf(cls, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Load a PDF.

        Try normal text extraction first.
        If the PDF appears to be scanned, automatically fall back to OCR.
        """
        text = cls._extract_pdf_text(file_path)

        if len(text) >= cls.OCR_MIN_CHARS:
            return text, {
                "extraction_method": "pypdf",
            }

        print(
            f"PDF appears to be scanned: {file_path.name}. "
            "Falling back to Vietnamese OCR..."
        )

        text = cls._ocr_pdf(file_path)

        return text, {
            "extraction_method": "ocr",
        }

    @staticmethod
    def load_markdown(file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Load Markdown with optional YAML frontmatter."""
        content = file_path.read_text(encoding="utf-8")

        match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n(.*)",
            content,
            re.DOTALL,
        )

        if match:
            metadata = yaml.safe_load(match.group(1)) or {}
            text = match.group(2).strip()
            return text, metadata

        return content.strip(), {}

    @classmethod
    def load(cls, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Load a supported document based on its file extension."""
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return cls.load_pdf(file_path)

        if suffix in [".md", ".markdown"]:
            return cls.load_markdown(file_path)

        raise ValueError(f"Unsupported file type: {suffix}")