from __future__ import annotations

import logging
import os
import re
import unicodedata

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader  # pypdf >= 3.x
except ImportError:
    try:
        from PyPDF2 import PdfReader  # type: ignore[no-redef]
    except ImportError:
        PdfReader = None  # type: ignore[assignment, misc]


class PDFProcessor:
    """Extract and clean text from PDF documents."""

    def __init__(self, ocr_enabled: bool = True) -> None:
        self.ocr_enabled = ocr_enabled
        if PdfReader is None:
            logger.warning(
                "Neither pypdf nor PyPDF2 is installed. "
                "PDF processing will not be available."
            )

    async def process_pdf(self, pdf_path: str) -> list[dict]:
        """Extract text from each page of a PDF file.

        Returns a list of ``{"page": int, "text": str, "metadata": dict}``.
        """
        if PdfReader is None:
            raise RuntimeError(
                "PDF library not available. Install pypdf or PyPDF2."
            )

        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        results: list[dict] = []
        try:
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages, start=1):
                raw_text = page.extract_text() or ""
                cleaned = self._clean_text(raw_text)
                results.append(
                    {
                        "page": page_num,
                        "text": cleaned,
                        "metadata": {
                            "source": os.path.basename(pdf_path),
                            "path": pdf_path,
                            "total_pages": len(reader.pages),
                        },
                    }
                )
        except Exception:
            logger.exception("Failed to process PDF: %s", pdf_path)
            raise

        logger.info("Processed %d pages from %s", len(results), pdf_path)
        return results

    async def process_directory(self, dir_path: str) -> list[dict]:
        """Process every PDF found in *dir_path* (non-recursive)."""
        if not os.path.isdir(dir_path):
            raise NotADirectoryError(f"Directory not found: {dir_path}")

        all_results: list[dict] = []
        pdf_files = sorted(
            f for f in os.listdir(dir_path) if f.lower().endswith(".pdf")
        )

        for filename in pdf_files:
            full_path = os.path.join(dir_path, filename)
            try:
                pages = await self.process_pdf(full_path)
                all_results.extend(pages)
            except Exception:
                logger.exception("Skipping file due to error: %s", full_path)

        logger.info(
            "Processed %d PDFs (%d total pages) from %s",
            len(pdf_files),
            len(all_results),
            dir_path,
        )
        return all_results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clean_text(self, text: str) -> str:
        """Remove extra whitespace and normalize Arabic characters."""
        # Normalize Unicode (NFC keeps composed Arabic forms)
        text = unicodedata.normalize("NFC", text)

        # Normalize common Arabic character variants
        text = re.sub(r"[\u0622\u0623\u0625]", "\u0627", text)  # alef variants -> alef
        text = re.sub(r"\u0629", "\u0647", text)                 # taa marbuta -> haa
        text = re.sub(r"[\u064B-\u065F]", "", text)              # remove tashkeel

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
