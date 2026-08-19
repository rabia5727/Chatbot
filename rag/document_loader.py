"""Safe in-memory text extraction for supported document formats."""

from __future__ import annotations

import io
import re
from pathlib import Path

from core.exceptions import DocumentProcessingError, UnsupportedDocumentTypeError

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
SUPPORTED_MIME_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
    ".txt": {"text/plain", "application/octet-stream"},
}


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [re.sub(r"[ \t]+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    return "\n\n".join(p for p in paragraphs if p).strip()


def _validate_type(filename: str, mime_type: str | None) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedDocumentTypeError("Only PDF, DOCX, and TXT documents are supported.")
    if mime_type and mime_type not in SUPPORTED_MIME_TYPES[extension]:
        raise UnsupportedDocumentTypeError(
            f"The MIME type '{mime_type}' does not match a supported {extension} document."
        )
    return extension


def extract_text(file_bytes: bytes, filename: str, mime_type: str | None = None) -> str:
    """Extract normalized text without writing the uploaded file to disk."""
    if not file_bytes:
        raise DocumentProcessingError("The uploaded document is empty.")
    extension = _validate_type(filename, mime_type)
    try:
        if extension == ".txt":
            try:
                text = file_bytes.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise DocumentProcessingError("TXT documents must use UTF-8 encoding.") from exc
        elif extension == ".pdf":
            import fitz

            with fitz.open(stream=file_bytes, filetype="pdf") as document:
                text = "\n\n".join(page.get_text("text") for page in document)
        else:
            from docx import Document

            document = Document(io.BytesIO(file_bytes))
            text = "\n\n".join(p.text for p in document.paragraphs if p.text.strip())
    except (DocumentProcessingError, UnsupportedDocumentTypeError):
        raise
    except Exception as exc:
        raise DocumentProcessingError(f"Could not read the uploaded {extension} document.") from exc

    normalized = _normalize_text(text)
    if not normalized:
        raise DocumentProcessingError("The document contains no extractable text.")
    return normalized
