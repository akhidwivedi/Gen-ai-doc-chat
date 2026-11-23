"""Text extraction for PDF, DOCX and TXT files."""
from dataclasses import dataclass
from pathlib import Path

import pymupdf  # PyMuPDF
from docx import Document as DocxDocument

from . import AIServiceError


@dataclass
class PageText:
    text: str
    page: int | None  # 1-based page number for PDFs, None for formats without pages


def extract_pdf(path: str) -> list[PageText]:
    pages: list[PageText] = []
    try:
        with pymupdf.open(path) as doc:
            if doc.needs_pass:
                raise AIServiceError("Password-protected PDFs are not supported.")
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if text:
                    pages.append(PageText(text=text, page=i))
    except AIServiceError:
        raise
    except Exception as exc:  # corrupt file, etc.
        raise AIServiceError(f"Could not read PDF: {exc}") from exc
    return pages


def extract_docx(path: str) -> list[PageText]:
    try:
        doc = DocxDocument(path)
    except Exception as exc:
        raise AIServiceError(f"Could not read DOCX: {exc}") from exc

    parts: list[str] = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    text = "\n".join(parts).strip()
    return [PageText(text=text, page=None)] if text else []


def extract_txt(path: str) -> list[PageText]:
    text = Path(path).read_text(encoding="utf-8", errors="replace").strip()
    return [PageText(text=text, page=None)] if text else []


_EXTRACTORS = {"pdf": extract_pdf, "docx": extract_docx, "txt": extract_txt}


def extract_text(path: str, file_type: str) -> list[PageText]:
    """Return non-empty text blocks (pages) from a document on disk."""
    extractor = _EXTRACTORS.get(file_type.lower())
    if extractor is None:
        raise AIServiceError(f"Unsupported file type: {file_type}")
    pages = extractor(path)
    if not pages:
        raise AIServiceError(
            "No extractable text found. Scanned/image-only documents are not supported."
        )
    return pages
