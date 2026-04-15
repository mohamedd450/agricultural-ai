"""PDF processing module for extracting text from agricultural PDF documents."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processes PDF files to extract text content and metadata."""

    def __init__(self) -> None:
        """Initialize the PDF processor."""
        try:
            import pdfplumber
            self._pdfplumber = pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed, PDF processing will be limited")
            self._pdfplumber = None

    def process_file(self, file_path: str) -> list[dict]:
        """Extract text and metadata from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of dicts with keys: page_num, text, source, language.
        """
        if self._pdfplumber is None:
            logger.error("pdfplumber is not available")
            return []

        results: list[dict] = []
        file_path = str(Path(file_path).resolve())

        try:
            with self._pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                        if not text.strip():
                            logger.info("Page %d has no text, attempting OCR fallback", i + 1)
                            text = self._ocr_fallback(page, file_path)
                        language = self._detect_language(text)
                        results.append({
                            "page_num": i + 1,
                            "text": text,
                            "source": file_path,
                            "language": language,
                        })
                    except Exception as e:
                        logger.error("Error processing page %d of %s: %s", i + 1, file_path, e)
                        results.append({
                            "page_num": i + 1,
                            "text": "",
                            "source": file_path,
                            "language": "unknown",
                        })
        except Exception as e:
            logger.error("Failed to open PDF %s: %s", file_path, e)

        return results

    def process_directory(self, dir_path: str) -> list[dict]:
        """Process all PDF files in a directory.

        Args:
            dir_path: Path to directory containing PDFs.

        Returns:
            Combined list of page results from all PDFs.
        """
        results: list[dict] = []
        dir_path = str(Path(dir_path).resolve())

        if not os.path.isdir(dir_path):
            logger.error("Directory not found: %s", dir_path)
            return results

        pdf_files = sorted(Path(dir_path).glob("*.pdf"))
        logger.info("Found %d PDF files in %s", len(pdf_files), dir_path)

        for pdf_file in pdf_files:
            logger.info("Processing: %s", pdf_file.name)
            file_results = self.process_file(str(pdf_file))
            results.extend(file_results)

        return results

    def _ocr_fallback(self, page: object, source: str) -> str:
        """Attempt OCR on a page when text extraction fails.

        Args:
            page: A pdfplumber page object.
            source: Source file path for logging.

        Returns:
            Extracted text from OCR or empty string.
        """
        try:
            from .ocr_engine import OCREngine
            engine = OCREngine()
            page_image = page.to_image(resolution=300)  # type: ignore[attr-defined]
            img = page_image.original
            return engine.extract_from_pdf_page(img, language="eng+ara")
        except Exception as e:
            logger.warning("OCR fallback failed for %s: %s", source, e)
            return ""

    @staticmethod
    def _detect_language(text: str) -> str:
        """Simple language detection based on character ranges.

        Args:
            text: Input text.

        Returns:
            Detected language: 'arabic', 'english', or 'mixed'.
        """
        if not text.strip():
            return "unknown"
        arabic_count = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
        latin_count = sum(1 for c in text if c.isascii() and c.isalpha())
        if arabic_count > latin_count:
            return "arabic"
        if latin_count > arabic_count:
            return "english"
        return "mixed"
