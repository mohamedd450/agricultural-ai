"""Book ingestion agent: load PDF/EPUB/TXT/DOCX into normalized text sections."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    try:
        from PyPDF2 import PdfReader  # type: ignore[no-redef]
    except Exception:  # pragma: no cover
        PdfReader = None  # type: ignore[assignment]

try:
    from ebooklib import epub
except Exception:  # pragma: no cover
    epub = None  # type: ignore[assignment]

try:
    import docx
except Exception:  # pragma: no cover
    docx = None  # type: ignore[assignment]

_SUPPORTED_EXTENSIONS = {".pdf", ".epub", ".txt", ".docx"}


@dataclass
class RawBook:
    """Normalized book content prior to structural parsing."""

    file_name: str
    file_path: str
    language: str
    text: str
    pages: list[dict]


class BookIngestionAgent:
    """Read books from disk and normalize their text representation."""

    def ingest(self, input_path: str) -> list[RawBook]:
        """Read supported book files from a file or directory path."""
        paths = self._resolve_input_paths(input_path)
        books: list[RawBook] = []

        for path in paths:
            ext = os.path.splitext(path)[1].lower()
            try:
                if ext == ".pdf":
                    text, pages = self._read_pdf(path)
                elif ext == ".epub":
                    text, pages = self._read_epub(path)
                elif ext == ".docx":
                    text, pages = self._read_docx(path)
                elif ext == ".txt":
                    text, pages = self._read_txt(path)
                else:
                    continue
            except Exception:
                logger.exception("Failed to ingest book: %s", path)
                continue

            cleaned_text = self._clean_text(text)
            books.append(
                RawBook(
                    file_name=os.path.basename(path),
                    file_path=path,
                    language=self._detect_language(cleaned_text),
                    text=cleaned_text,
                    pages=pages,
                )
            )

        return books

    def _resolve_input_paths(self, input_path: str) -> list[str]:
        if os.path.isfile(input_path):
            return [input_path] if self._is_supported(input_path) else []

        if not os.path.isdir(input_path):
            raise FileNotFoundError(f"Input path does not exist: {input_path}")

        paths: list[str] = []
        for name in sorted(os.listdir(input_path)):
            full = os.path.join(input_path, name)
            if os.path.isfile(full) and self._is_supported(full):
                paths.append(full)
        return paths

    @staticmethod
    def _is_supported(path: str) -> bool:
        return os.path.splitext(path)[1].lower() in _SUPPORTED_EXTENSIONS

    def _read_pdf(self, path: str) -> tuple[str, list[dict]]:
        if PdfReader is None:
            raise RuntimeError("PDF parsing requires pypdf or PyPDF2")

        reader = PdfReader(path)
        pages: list[dict] = []
        texts: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if page_text:
                texts.append(page_text)
                pages.append({"page": index, "text": page_text})
        return "\n\n".join(texts), pages

    def _read_txt(self, path: str) -> tuple[str, list[dict]]:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            text = file.read()
        return text, [{"page": 1, "text": text}]

    def _read_docx(self, path: str) -> tuple[str, list[dict]]:
        if docx is None:
            raise RuntimeError("DOCX parsing requires python-docx")

        document = docx.Document(path)
        parts = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        text = "\n".join(parts)
        return text, [{"page": 1, "text": text}]

    def _read_epub(self, path: str) -> tuple[str, list[dict]]:
        if epub is None:
            raise RuntimeError("EPUB parsing requires ebooklib")

        book = epub.read_epub(path)
        texts: list[str] = []
        pages: list[dict] = []
        section_num = 0
        for item in book.get_items():
            body: Optional[bytes] = getattr(item, "content", None)
            if not body:
                continue
            decoded = body.decode("utf-8", errors="ignore")
            chunk = re.sub(r"<[^>]+>", " ", decoded)
            chunk = self._clean_text(chunk)
            if not chunk:
                continue
            section_num += 1
            texts.append(chunk)
            pages.append({"page": section_num, "text": chunk})

        return "\n\n".join(texts), pages

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text or "").strip()
        return text

    @staticmethod
    def _detect_language(text: str) -> str:
        if not text:
            return "ar"
        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        latin_chars = len(re.findall(r"[A-Za-z]", text))
        return "ar" if arabic_chars >= latin_chars else "en"
